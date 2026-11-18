"""Observe browser input without changing the application's state."""
import asyncio
from datetime import datetime,timezone


INIT_SCRIPT=r"""(() => {
 const documentId=String(performance.timeOrigin)+'-'+Math.random().toString(36).slice(2);
 window.__wcagExpectedPointerTarget=null;
 const types=['pointerdown','pointerup','pointercancel','pointermove','mousedown','mouseup','click',
              'dragstart','dragover','drop','dragend','keydown','keyup'];
 for(const type of types) addEventListener(type,event=>{
  if(type==='pointermove'&&window.__wcagObservePointerMove!==true)return;
  const path=event.composedPath(),target=path.find(n=>n?.nodeType===1);
  const data={type:event.type,isTrusted:event.isTrusted,documentId,url:location.href,
   timestamp:event.timeStamp,target:target?{tag:target.localName,id:target.id}:null,
   pointerType:event.pointerType??null,button:event.button??null,buttons:event.buttons??null,
   x:event.clientX??null,y:event.clientY??null,
   expectedTargetMatched:window.__wcagExpectedPointerTarget===null?null:path.includes(window.__wcagExpectedPointerTarget)};
  if(event instanceof KeyboardEvent){
   data.key=event.key.length===1?'[character]':event.key;
   data.modifiers={control:event.ctrlKey,alt:event.altKey,shift:event.shiftKey,meta:event.metaKey};
  }
  window.__wcagAuditInput(data).catch(()=>{});
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
        await locator_for(page,action).evaluate('(element)=>{window.__wcagExpectedPointerTarget=element}')
        index=len(observer.events)
        await page.mouse.down(button=action.get('button','left'))
        await observer.pointer_down_after(index)
    elif kind=='pointer_up':
        await page.mouse.up(button=action.get('button','left'))
    elif kind=='drag':
        await locator_for(page,action).drag_to(locator_for(page,action['target']))
    else:raise ValueError('未対応のポインター操作: '+kind)
