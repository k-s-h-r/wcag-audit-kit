"""Observe browser input without changing the application's state."""
import asyncio
from datetime import datetime,timezone
from urllib.parse import urldefrag


INIT_SCRIPT=r"""(() => {
 const documentId=String(performance.timeOrigin)+'-'+Math.random().toString(36).slice(2);
 window.__wcagExpectedInputTarget=null;
 const targetOf=event=>event.composedPath().find(node=>node?.nodeType===1);
 const record=(event,target,data={})=>window.__wcagAuditInput({
  type:event.type,isTrusted:event.isTrusted,documentId,url:location.href,timestamp:event.timeStamp,
  target:target?{tag:target.localName,id:target.id}:null,...data
 }).catch(()=>{});
 let tabTrace=false,tab=null,focus=null,lastNavigation=null,navigationId=0;
 if(window===window.top){
  window.__wcagStartTabFocusTrace=()=>{tabTrace=true;};
  for(const type of ['focus','focusin']) addEventListener(type,event=>{
   if(!tab||tab.eventPhase!==Event.NONE||!event.isTrusted)return;
   const target=targetOf(event);
   if(!target)return;
   focus={event,target};
   record(event,target);
  },{capture:true,passive:true});
  window.navigation?.addEventListener('navigate',event=>{
   if(!tabTrace||!event.isTrusted)return;
   // Also keep other attempts. A canceled focus navigation and a subsequent
   // activation can request the same URL, so the guard alone cannot join them.
   const activeFocus=tab&&focus?.event.eventPhase ? focus : null;
   lastNavigation={event,id:++navigationId};
   record(event,activeFocus?.target,{focusType:activeFocus?.event.type??null,
    focusDispatchPhase:activeFocus?.event.eventPhase??Event.NONE,navigationId,
    destination:event.destination.url,
    sameDocument:event.destination.sameDocument,hashChange:event.hashChange});
  },{capture:true,passive:true});
 }
 const types=['pointerdown','pointerup','pointercancel','pointermove','mousedown','mouseup','click',
              'dragstart','dragover','drop','dragend','keydown','keyup'];
 for(const type of types) addEventListener(type,function wcagAuditInputListener(event){
  if(type==='pointermove'&&window.__wcagObservePointerMove!==true)return;
  const path=event.composedPath(),target=path.find(n=>n?.nodeType===1);
  const data={
   pointerType:event.pointerType??null,button:event.button??null,buttons:event.buttons??null,
   x:event.clientX??null,y:event.clientY??null,
   expectedTargetMatched:window.__wcagExpectedInputTarget===null?null:path.includes(window.__wcagExpectedInputTarget)};
  if(event.type==='click'&&event.isTrusted&&data.expectedTargetMatched&&event.pointerType==='mouse'){
   const value=window.__wcagFunctionValueAtClick?.();
   if(typeof value==='string') data.functionValueAtClick=value;
  }
  if(event instanceof KeyboardEvent){
   data.key=event.key.length===1?'[character]':event.key;
   data.modifiers={control:event.ctrlKey,alt:event.altKey,shift:event.shiftKey,meta:event.metaKey};
  }
  if(tabTrace&&event.isTrusted){
   if(tab&&type==='keyup'&&event.key==='Tab'&&lastNavigation){
    const attempted=lastNavigation.event;
    data.navigationAtKeyup={id:lastNavigation.id,dispatchEnded:attempted.eventPhase===Event.NONE,
     canceled:attempted.defaultPrevented,aborted:attempted.signal.aborted};
   }
   tab=type==='keydown'&&event.key==='Tab'&&!event.repeat&&!event.ctrlKey&&!event.altKey
    &&!event.shiftKey&&!event.metaKey?event:null;
   focus=null;
   lastNavigation=null;
  }
  record(event,target,data);
 },{capture:true,passive:true});
})();"""


class InputObserver:
    def __init__(self,limit=10000):
        self.limit=limit;self.events=[];self.dropped=0;self.changed=asyncio.Event()
        self.event_frames=[]

    def accept(self,source,event):
        if len(self.events)>=self.limit:self.dropped+=1
        else:
            self.events.append(dict(event,is_main_frame=source['frame']==source['page'].main_frame,
                                    received_at=datetime.now(timezone.utc).isoformat()))
            self.event_frames.append(source['frame'])
        self.changed.set()

    async def pointer_down_after(self,index,timeout=2):
        deadline=asyncio.get_running_loop().time()+timeout
        while True:
            self.changed.clear()
            events=[e for e in self.events[index:] if e['type']=='pointerdown']
            if events:
                event=events[0]
                if event.get('isTrusted') is not True or event.get('expectedTargetMatched') is not True:
                    raise ValueError('押下が指定した対象へ実ブラウザーの入力として届いていない')
                return event
            remaining=deadline-asyncio.get_running_loop().time()
            if remaining<=0:raise ValueError('対象へのpointerdownを観測できない')
            try:await asyncio.wait_for(self.changed.wait(),remaining)
            except TimeoutError:raise ValueError('対象へのpointerdownを観測できない') from None

    def export(self):
        return {'events':self.events,'truncated':bool(self.dropped),'dropped':self.dropped,
                'note':'ブラウザー自動操作の入力イベント。物理端末の操作又はWCAG基準全体の判定ではない。'}


def blocked_tab_focus(observer, first_event, blocked, source_url):
    """Join the same-step input, synchronous focus dispatch, and guard decision."""
    if observer.dropped or len(blocked) != 1:
        return None
    request = blocked[0]
    if (request.get('is_main_frame') is not True or request.get('resource_type') != 'document'
            or request.get('reason') != 'navigation_out_of_scope' or request['method'] != 'GET'):
        return None
    sequence = list(enumerate(observer.events[first_event:], first_event))
    navigation = [(index, event) for index, event in sequence if event['type'] == 'navigate']
    if len(navigation) != 1:
        return None
    navigation_index, attempt = navigation[0]
    if (attempt.get('focusDispatchPhase') not in (1, 2, 3)
            or attempt.get('sameDocument') is not False or attempt.get('hashChange') is not False
            or urldefrag(attempt['destination'])[0] != urldefrag(request['url'])[0]):
        return None
    preceding = sequence[:navigation_index - first_event]
    if len(preceding) < 2:
        return None
    released = [(index, event) for index, event in sequence if event['type'] == 'keyup']
    if len(released) != 1:
        return None
    keyup_index, keyup = released[0]
    expected_at_keyup = {'id': attempt.get('navigationId'), 'dispatchEnded': True, 'canceled': False, 'aborted': False}
    if (keyup_index <= navigation_index or keyup.get('key') != 'Tab' or expected_at_keyup['id'] is None
            or keyup.get('navigationAtKeyup') != expected_at_keyup):
        return None
    key_index, key = preceding[0]
    focus_index, focus = preceding[-1]
    if (key['type'] != 'keydown' or key.get('key') != 'Tab' or any(key.get('modifiers', {}).values())
            or focus['type'] not in {'focus', 'focusin'} or focus['type'] != attempt.get('focusType')
            or not focus['target'] or focus['target'] != attempt['target']
            or any(event['type'] not in {'focus', 'focusin'} for _, event in preceding[1:])
            or any(not event['isTrusted'] or not event['is_main_frame'] or event['url'] != source_url
                   or event['documentId'] != key['documentId'] for _, event in [*preceding, navigation[0], released[0]])):
        return None
    return {'status': 'blocked', 'source_url': source_url, 'target': focus['target'],
            'destination': attempt['destination'], 'input_evidence': 'input-events.json',
            'keydown_event_index': key_index, 'focus_event_index': focus_index,
            'navigation_event_index': navigation_index, 'keyup_event_index': keyup_index, 'blocked_request_index': 0}


def locator_for(page,action):
    scope=page.frame_locator(action['frame']) if action.get('frame') else page
    return scope.get_by_role(action['role'],name=action['name'],exact=True) if 'role' in action else scope.locator(action['selector'])


async def pointer_action(page,action,observer):
    kind=action['type']
    if kind=='pointer_move':
        if 'x' in action or 'y' in action:
            await page.mouse.move(action['x'],action['y'],steps=action.get('steps',1))
        else:
            options={'position':action['position']} if 'position' in action else {}
            await locator_for(page,action).hover(**options)
    elif kind=='pointer_down':
        # Set only the observer's expected element; do not move or focus it.
        await locator_for(page,action).evaluate('(element)=>{window.__wcagExpectedInputTarget=element}')
        index=len(observer.events)
        await page.mouse.down(button=action.get('button','left'))
        await observer.pointer_down_after(index)
    elif kind=='pointer_up':
        await page.mouse.up(button=action.get('button','left'))
    elif kind=='drag':
        await locator_for(page,action).drag_to(locator_for(page,action['target']))
    else:raise ValueError('未対応のポインター操作: '+kind)
