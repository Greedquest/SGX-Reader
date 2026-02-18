#!/usr/bin/env python3
"""
Compare extracted stencil types with the converter's STENCIL_MAPPING.
"""

# Current STENCIL_MAPPING from signavio_to_bpmn.py
STENCIL_MAPPING = {
    # Diagram root
    'BPMNDiagram': 'definitions',

    # Participants
    'Pool': 'participant',
    'VerticalPool': 'participant',
    'CollapsedPool': 'participant',
    'CollapsedVerticalPool': 'participant',
    'Lane': 'lane',
    'VerticalLane': 'lane',

    # Tasks
    'Task': 'task',
    'CollapsedSubprocess': 'subProcess',
    'Subprocess': 'subProcess',
    'EventSubprocess': 'subProcess',

    # Gateways
    'Exclusive_Databased_Gateway': 'exclusiveGateway',
    'ParallelGateway': 'parallelGateway',
    'AND_Gateway': 'parallelGateway',
    'InclusiveGateway': 'inclusiveGateway',
    'EventbasedGateway': 'eventBasedGateway',
    'ComplexGateway': 'complexGateway',

    # Start Events
    'StartNoneEvent': 'startEvent',
    'StartEvent': 'startEvent',
    'StartMessageEvent': 'startEvent',
    'StartTimerEvent': 'startEvent',
    'StartConditionalEvent': 'startEvent',
    'StartSignalEvent': 'startEvent',
    'StartErrorEvent': 'startEvent',
    'StartMultipleEvent': 'startEvent',
    'StartParallelMultipleEvent': 'startEvent',

    # End Events
    'EndNoneEvent': 'endEvent',
    'EndEvent': 'endEvent',
    'EndMessageEvent': 'endEvent',
    'EndEscalationEvent': 'endEvent',
    'EndErrorEvent': 'endEvent',
    'EndTerminateEvent': 'endEvent',
    'EndCancelEvent': 'endEvent',
    'EndSignalEvent': 'endEvent',

    # Intermediate Events - Catching
    'IntermediateEvent': 'intermediateCatchEvent',
    'IntermediateMessageEventCatching': 'intermediateCatchEvent',
    'IntermediateTimerEvent': 'intermediateCatchEvent',
    'IntermediateConditionalEvent': 'intermediateCatchEvent',
    'IntermediateSignalEventCatching': 'intermediateCatchEvent',
    'IntermediateLinkEventCatching': 'intermediateCatchEvent',
    'IntermediateErrorEvent': 'intermediateCatchEvent',
    'IntermediateCancelEvent': 'intermediateCatchEvent',
    'IntermediateMultipleEventCatching': 'intermediateCatchEvent',
    'IntermediateParallelMultipleEventCatching': 'intermediateCatchEvent',
    'IntermediateCompensationEventCatching': 'intermediateCatchEvent',

    # Intermediate Events - Throwing
    'IntermediateMessageEventThrowing': 'intermediateThrowEvent',
    'IntermediateSignalEventThrowing': 'intermediateThrowEvent',
    'IntermediateLinkEventThrowing': 'intermediateThrowEvent',
    'IntermediateCompensationEventThrowing': 'intermediateThrowEvent',
    'IntermediateEscalationEvent': 'intermediateThrowEvent',
    'IntermediateEscalationEventThrowing': 'intermediateThrowEvent',

    # Flows
    'SequenceFlow': 'sequenceFlow',
    'MessageFlow': 'messageFlow',
    'Association_Unidirectional': 'association',
    'Association_Undirected': 'association',
    'Association_Bidirectional': 'association',
    'ConversationLink': 'conversationLink',

    # Data
    'DataObject': 'dataObjectReference',
    'DataStore': 'dataStoreReference',
    'Message': 'message',

    # Artifacts
    'TextAnnotation': 'textAnnotation',
    'Group': 'group',

    # Choreography
    'ChoreographyTask': 'choreographyTask',
    'ChoreographyParticipant': 'participant',
    'ChoreographySubprocessCollapsed': 'subChoreography',
    'ChoreographySubprocessExpanded': 'subChoreography',

    # Conversation
    'Communication': 'conversation',
    'Participant': 'participant',

    # Signavio-specific
    'ITSystem': 'dataStoreReference',
    'processparticipant': 'dataObjectReference',
}

# Stencil types found in actual JSON files (from extract_stencils.py)
ACTUAL_STENCILS = [
    'SequenceFlow',
    'Task',
    'Exclusive_Databased_Gateway',
    'MessageFlow',
    'Lane',
    'Association_Unidirectional',
    'EndNoneEvent',
    'Association_Undirected',
    'Pool',
    'DataObject',
    'BPMNDiagram',
    'IntermediateMessageEventCatching',
    'StartNoneEvent',
    'ParallelGateway',
    'ITSystem',
    'TextAnnotation',
    'CollapsedSubprocess',
    'CollapsedPool',
    'IntermediateTimerEvent',
    'IntermediateMessageEventThrowing',
    'StartMessageEvent',
    'EventbasedGateway',
    'DataStore',
    'EndMessageEvent',
    'ChoreographyParticipant',
    'processparticipant',
    'InclusiveGateway',
    'Message',
    'IntermediateEscalationEvent',
    'EndEscalationEvent',
    'ChoreographyTask',
    'EndTerminateEvent',
    'StartTimerEvent',
    'Subprocess',
    'EndEvent',
    'IntermediateErrorEvent',
    'StartEvent',
    'EndErrorEvent',
    'IntermediateEvent',
    'AND_Gateway',
    'Association_Bidirectional',
    'ConversationLink',
    'EventSubprocess',
    'StartConditionalEvent',
    'EndCancelEvent',
    'IntermediateConditionalEvent',
    'IntermediateSignalEventCatching',
    'EndSignalEvent',
    'Communication',
    'Group',
    'IntermediateMultipleEventCatching',
    'IntermediateSignalEventThrowing',
    'Participant',
    'IntermediateLinkEventCatching',
    'IntermediateLinkEventThrowing',
    'ComplexGateway',
    'IntermediateCompensationEventThrowing',
    'VerticalLane',
    'ChoreographySubprocessCollapsed',
    'IntermediateCancelEvent',
    'IntermediateParallelMultipleEventCatching',
    'StartMultipleEvent',
    'IntermediateCompensationEventCatching',
    'StartErrorEvent',
    'StartSignalEvent',
    'ChoreographySubprocessExpanded',
    'CollapsedVerticalPool',
    'IntermediateEscalationEventThrowing',
    'StartParallelMultipleEvent',
    'VerticalPool',
]


def main():
    actual_set = set(ACTUAL_STENCILS)
    mapped_set = set(STENCIL_MAPPING.keys())

    in_data_not_mapped = actual_set - mapped_set
    in_mapping_not_data = mapped_set - actual_set
    covered = actual_set & mapped_set

    print("=" * 70)
    print("STENCIL MAPPING COVERAGE ANALYSIS")
    print("=" * 70)

    print(f"\nActual stencils found in JSON files: {len(actual_set)}")
    print(f"Stencils in STENCIL_MAPPING:         {len(mapped_set)}")
    print(f"Covered (in both):                   {len(covered)}")

    print(f"\n{'=' * 70}")
    print("MISSING FROM MAPPING (found in data but not mapped)")
    print(f"{'=' * 70}")
    if in_data_not_mapped:
        for stencil in sorted(in_data_not_mapped):
            print(f"  - {stencil}")
    else:
        print("  None! All stencils are mapped.")

    print(f"\n{'=' * 70}")
    print("EXTRA IN MAPPING (mapped but not found in data)")
    print(f"{'=' * 70}")
    if in_mapping_not_data:
        for stencil in sorted(in_mapping_not_data):
            print(f"  - {stencil} -> {STENCIL_MAPPING[stencil]}")
    else:
        print("  None! All mappings are used.")

    print(f"\n{'=' * 70}")
    print("COMPLETE MAPPING TABLE")
    print(f"{'=' * 70}")
    print(f"{'Signavio Stencil':<45} {'BPMN 2.0 Element':<25}")
    print("-" * 70)

    for stencil in sorted(actual_set):
        bpmn_element = STENCIL_MAPPING.get(stencil, '** UNMAPPED **')
        marker = "" if stencil in mapped_set else " <-- NEEDS MAPPING"
        print(f"{stencil:<45} {bpmn_element:<25}{marker}")


if __name__ == '__main__':
    main()
