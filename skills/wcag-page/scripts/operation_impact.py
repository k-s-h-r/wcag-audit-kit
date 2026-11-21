"""Record one operation's DOM changes and reuse strictly element-local axe evidence."""
from hashlib import sha256

RESULT_TYPES = ('violations', 'incomplete', 'passes', 'inapplicable')
AXE_VERSION = '4.11.0'
LOCAL_SELECTORS = {'aria-valid-attr': '*', 'tabindex': '[tabindex]'}
MAX_REUSED_PER_RULE = 256
MODAL_STATE_CHANGED = 'axe検査の前後でネイティブのモーダルの状態が変わった。画面と同じ状態で再検査する。'

RUN_AXE = """
async ({version, selectors, resultTypes, modalState}) => {
  const sameModalState = () => {
    if (modalState === null) return true;
    const current = window.__wcagExplore('native-modal-state');
    return current.generation === modalState.generation &&
      JSON.stringify(current.selectors) === JSON.stringify(modalState.selectors);
  };
  if (!sameModalState()) return {modalChanged:true};
  const hasSelectors = Object.keys(selectors).length > 0;
  // A native modal makes the rest of the document inert without changing its HTML.
  const nativeModal = hasSelectors && document.querySelector('dialog:modal') !== null;
  const scan = async narrowed => {
    const results = await axe.run(document, {resultTypes});
    return sameModalState() ? {narrowed, nativeModal, results} : {modalChanged:true};
  };
  if (hasSelectors && !nativeModal && axe.version === version) {
    try {
      axe.configure({rules: Object.entries(selectors).map(([id, selector]) => ({id, selector}))});
      return await scan(true);
    } catch {
      axe.reset();
    }
  }
  return await scan(false);
}
"""


def compact(data):
    """Persist fingerprints instead of duplicating element HTML in the ledger."""
    for key in ('operation_inputs', 'operation_reference_inputs'):
        data[key] = {target: sha256(value.encode()).hexdigest() for target, value in data.get(key, {}).items()}


def difference(before, after, action, mutations, *, new_document=False):
    old = {item['selector']: item for item in before['state']}
    new = {item['selector']: item for item in after['state']}
    appeared = new.keys() - old.keys()
    disappeared = old.keys() - new.keys()
    changed = {target for target in old.keys() & new.keys() if old[target] != new[target]}
    old_references, new_references = before['operation_reference_inputs'], after['operation_reference_inputs']
    changed.update(target for target in old_references.keys() | new_references.keys()
                   if old_references.get(target) != new_references.get(target))
    mutated = set(mutations['targets'])
    direct = appeared | disappeared | changed | mutated | {action['selector']}
    related = set()
    for controller, target, _attribute in before['operation_relations'] + after['operation_relations']:
        if controller in direct:
            related.add(target)
        if target in direct:
            related.add(controller)
    focus = {'before': before['operation_focus'], 'after': after['operation_focus']}
    return {
        'action': {key: action[key] for key in ('selector', 'type', 'key') if key in action},
        'appeared': sorted(appeared), 'disappeared': sorted(disappeared),
        'changed': sorted(changed), 'mutated': sorted(mutated), 'related': sorted(related - direct),
        'focus': focus, 'mutation_limit_reached': mutations['truncated'], 'new_document': new_document,
    }



def can_reuse(before, after, impact):
    return (not impact['new_document'] and not impact['mutation_limit_reached']
            and before['url'] == after['url']
            and before['operation_scope_supported'] and after['operation_scope_supported'])


def target_lists(results, rules):
    targets = {rule_id: [] for rule_id in rules}
    for category in RESULT_TYPES[:-1]:
        for rule in results[category]:
            if rule['id'] in targets:
                targets[rule['id']].extend(node['target'] for node in rule['nodes'])
    return targets

def reusable_nodes(before, after, baseline, results, impact):
    excluded = {impact['action']['selector'], *impact['focus'].values()}
    for key in ('appeared', 'disappeared', 'changed', 'mutated', 'related'):
        excluded.update(impact[key])
    prior = baseline.get('operation_inputs', {})
    observed = before['operation_inputs']
    unchanged = {target for target, digest in after['operation_inputs'].items()
                 if target not in excluded and digest == observed.get(target) == prior.get(target)}

    reused = {rule_id: {} for rule_id in LOCAL_SELECTORS}
    limit = {rule_id: MAX_REUSED_PER_RULE for rule_id in LOCAL_SELECTORS}
    for category in RESULT_TYPES[:-1]:
        for rule in results[category]:
            rule_id = rule['id']
            if not limit.get(rule_id):
                continue
            nodes = [node for node in rule['nodes']
                     if len(node['target']) == 1 and isinstance(node['target'][0], str)
                     and node['target'][0] in unchanged][:limit[rule_id]]
            if nodes:
                reused[rule_id][category] = dict(rule, nodes=nodes)
                limit[rule_id] -= len(nodes)
    return {rule_id: entries for rule_id, entries in reused.items() if entries}


def merge(results, reused, order):
    # Preserve the standard axe category records and node counts for all readers.
    rank = {impact: index for index, impact in enumerate((None, 'minor', 'moderate', 'serious', 'critical'))}
    for rule_id, old in reused.items():
        results['inapplicable'] = [rule for rule in results['inapplicable'] if rule['id'] != rule_id]
        for category, entry in old.items():
            current = next((rule for rule in results[category] if rule['id'] == rule_id), None)
            if current is None:
                current = dict(entry, nodes=[])
                results[category].append(current)
                results[category].sort(key=lambda rule: rule['id'])
            current['nodes'].extend(entry['nodes'])
            current['nodes'].sort(key=lambda node: order.get(node['target'][0], len(order))
                                  if len(node['target']) == 1 and isinstance(node['target'][0], str)
                                  else len(order))
            current['impact'] = max((node['impact'] for node in current['nodes']), key=rank.__getitem__)


async def _scan(page, args):
    audited = await page.evaluate(RUN_AXE, args)
    if audited.get('modalChanged'):
        raise ValueError(MODAL_STATE_CHANGED)
    return audited


async def run_axe(page, data, reused):
    selectors = {}
    for rule_id, entries in reused.items():
        excluded = [node['target'][0] for entry in entries.values() for node in entry['nodes']]
        selectors[rule_id] = LOCAL_SELECTORS[rule_id] + ':not(' + ','.join(excluded) + ')'
    modal_state = (dict(selectors=data.get('native_modals', []), generation=data['dialog_generation'])
                   if data['operation_scope_supported'] else None)
    args = dict(version=AXE_VERSION, selectors=selectors, resultTypes=RESULT_TYPES, modalState=modal_state)
    audited = await _scan(page, args)
    whole_scope = {'mode': 'whole_page'}
    if not audited['narrowed']:
        if audited.get('nativeModal'):
            whole_scope['reason'] = 'native_modal'
        return audited['results'], whole_scope
    current = await page.evaluate("""() => ({...window.__wcagExplore('inputs'), url: location.href,
      modalState: window.__wcagExplore('native-modal-state')})""")
    compact(current)
    if modal_state is not None and current['modalState'] != modal_state:
        raise ValueError(MODAL_STATE_CHANGED)
    # An ongoing callback or stylesheet update can invalidate the comparison during axe.
    if (current['url'] != data['url'] or not current['operation_scope_supported'] or
            current['operation_inputs'] != data['operation_inputs']):
        await page.evaluate('() => axe.reset()')
        full = await _scan(page, dict(args, selectors={}))
        return full['results'], whole_scope
    order = {item['selector']: index for index, item in enumerate(data['state'])}
    results = audited['results']
    observed = target_lists(results, reused)
    merge(results, reused, order)
    return results, {
        'mode': 'mixed',
        'rechecked': observed,
        'reused': {rule_id: sorted(node['target'][0] for entry in entries.values() for node in entry['nodes'])
                   for rule_id, entries in reused.items()},
    }
