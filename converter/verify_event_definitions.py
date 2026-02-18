#!/usr/bin/env python3
"""
Verify that all event stencils have proper event definitions.
"""

# Events found in data (from extract_stencils.py)
EVENT_STENCILS_IN_DATA = {
    # Start Events
    'StartNoneEvent': 747,
    'StartEvent': 36,
    'StartMessageEvent': 294,
    'StartTimerEvent': 54,
    'StartConditionalEvent': 12,
    'StartSignalEvent': 2,
    'StartErrorEvent': 2,
    'StartMultipleEvent': 3,
    'StartParallelMultipleEvent': 1,

    # End Events
    'EndNoneEvent': 1505,
    'EndEvent': 48,
    'EndMessageEvent': 155,
    'EndEscalationEvent': 69,
    'EndErrorEvent': 29,
    'EndTerminateEvent': 58,
    'EndCancelEvent': 11,
    'EndSignalEvent': 9,

    # Intermediate Catching Events
    'IntermediateEvent': 22,
    'IntermediateMessageEventCatching': 789,
    'IntermediateTimerEvent': 352,
    'IntermediateConditionalEvent': 11,
    'IntermediateSignalEventCatching': 10,
    'IntermediateLinkEventCatching': 6,
    'IntermediateErrorEvent': 47,
    'IntermediateCancelEvent': 3,
    'IntermediateMultipleEventCatching': 8,
    'IntermediateParallelMultipleEventCatching': 3,
    'IntermediateCompensationEventCatching': 2,

    # Intermediate Throwing Events
    'IntermediateMessageEventThrowing': 301,
    'IntermediateSignalEventThrowing': 7,
    'IntermediateLinkEventThrowing': 6,
    'IntermediateCompensationEventThrowing': 5,
    'IntermediateEscalationEvent': 76,
    'IntermediateEscalationEventThrowing': 1,
}

# Current EVENT_DEFINITIONS from converter
EVENT_DEFINITIONS = {
    'StartMessageEvent': 'messageEventDefinition',
    'StartTimerEvent': 'timerEventDefinition',
    'StartConditionalEvent': 'conditionalEventDefinition',
    'StartSignalEvent': 'signalEventDefinition',
    'StartErrorEvent': 'errorEventDefinition',
    'StartMultipleEvent': 'multipleEventDefinition',
    'StartParallelMultipleEvent': 'parallelMultipleEventDefinition',
    'EndMessageEvent': 'messageEventDefinition',
    'EndEscalationEvent': 'escalationEventDefinition',
    'EndErrorEvent': 'errorEventDefinition',
    'EndTerminateEvent': 'terminateEventDefinition',
    'EndCancelEvent': 'cancelEventDefinition',
    'EndSignalEvent': 'signalEventDefinition',
    'IntermediateMessageEventCatching': 'messageEventDefinition',
    'IntermediateMessageEventThrowing': 'messageEventDefinition',
    'IntermediateTimerEvent': 'timerEventDefinition',
    'IntermediateConditionalEvent': 'conditionalEventDefinition',
    'IntermediateSignalEventCatching': 'signalEventDefinition',
    'IntermediateSignalEventThrowing': 'signalEventDefinition',
    'IntermediateLinkEventCatching': 'linkEventDefinition',
    'IntermediateLinkEventThrowing': 'linkEventDefinition',
    'IntermediateErrorEvent': 'errorEventDefinition',
    'IntermediateCancelEvent': 'cancelEventDefinition',
    'IntermediateCompensationEventCatching': 'compensateEventDefinition',
    'IntermediateCompensationEventThrowing': 'compensateEventDefinition',
    'IntermediateEscalationEvent': 'escalationEventDefinition',
    'IntermediateEscalationEventThrowing': 'escalationEventDefinition',
}


def main():
    print("=" * 70)
    print("EVENT DEFINITION COVERAGE ANALYSIS")
    print("=" * 70)

    # Events that need definitions (non-None events)
    needs_definition = {k for k in EVENT_STENCILS_IN_DATA.keys()
                       if 'None' not in k and k not in ('StartEvent', 'EndEvent', 'IntermediateEvent')}

    has_definition = set(EVENT_DEFINITIONS.keys())

    missing = needs_definition - has_definition
    extra = has_definition - set(EVENT_STENCILS_IN_DATA.keys())

    print(f"\nEvents needing definitions: {len(needs_definition)}")
    print(f"Events with definitions:    {len(has_definition)}")

    print(f"\n{'=' * 70}")
    print("EVENTS MISSING DEFINITIONS (need to add)")
    print(f"{'=' * 70}")
    if missing:
        for stencil in sorted(missing):
            count = EVENT_STENCILS_IN_DATA.get(stencil, 0)
            suggested = guess_event_definition(stencil)
            print(f"  {stencil} ({count} occurrences)")
            print(f"    -> Suggested: {suggested}")
    else:
        print("  None! All events have definitions.")

    print(f"\n{'=' * 70}")
    print("EVENTS WITH DEFINITIONS NOT IN DATA")
    print(f"{'=' * 70}")
    if extra:
        for stencil in sorted(extra):
            print(f"  {stencil} -> {EVENT_DEFINITIONS[stencil]}")
    else:
        print("  None! All defined events appear in data.")

    print(f"\n{'=' * 70}")
    print("NONE EVENTS (no definition needed)")
    print(f"{'=' * 70}")
    none_events = [k for k in EVENT_STENCILS_IN_DATA.keys()
                   if 'None' in k or k in ('StartEvent', 'EndEvent', 'IntermediateEvent')]
    for stencil in sorted(none_events):
        count = EVENT_STENCILS_IN_DATA[stencil]
        print(f"  {stencil}: {count} occurrences")


def guess_event_definition(stencil):
    """Guess the appropriate event definition based on stencil name."""
    name = stencil.lower()
    if 'message' in name:
        return 'messageEventDefinition'
    elif 'timer' in name:
        return 'timerEventDefinition'
    elif 'conditional' in name:
        return 'conditionalEventDefinition'
    elif 'signal' in name:
        return 'signalEventDefinition'
    elif 'error' in name:
        return 'errorEventDefinition'
    elif 'escalation' in name:
        return 'escalationEventDefinition'
    elif 'cancel' in name:
        return 'cancelEventDefinition'
    elif 'compensation' in name:
        return 'compensateEventDefinition'
    elif 'terminate' in name:
        return 'terminateEventDefinition'
    elif 'link' in name:
        return 'linkEventDefinition'
    elif 'multiple' in name and 'parallel' in name:
        return '(multiple parallel event definitions)'
    elif 'multiple' in name:
        return '(multiple event definitions)'
    else:
        return '(unknown)'


if __name__ == '__main__':
    main()
