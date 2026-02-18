# Signavio to BPMN 2.0 Stencil Mapping Reference

This document provides a complete mapping from Signavio stencil IDs to BPMN 2.0 XML elements.
Based on analysis of 915 JSON files containing 43,605 stencil occurrences.

## Summary Statistics

| Category | Count |
|----------|-------|
| Total unique stencil types | 70 |
| Mapping coverage | 100% |

---

## Mapping Tables by Category

### Diagram Root

| Signavio Stencil | BPMN 2.0 Element | Occurrences | Notes |
|------------------|------------------|-------------|-------|
| `BPMNDiagram` | `definitions` | 898 | Root element of the XML |

---

### Participants & Lanes

| Signavio Stencil | BPMN 2.0 Element | Occurrences | Notes |
|------------------|------------------|-------------|-------|
| `Pool` | `participant` | 965 | Horizontal pool |
| `VerticalPool` | `participant` | 1 | Vertical orientation |
| `CollapsedPool` | `participant` | 368 | Black-box pool, no processRef |
| `CollapsedVerticalPool` | `participant` | 1 | Vertical black-box pool |
| `Lane` | `lane` | 1,872 | Horizontal lane |
| `VerticalLane` | `lane` | 4 | Vertical lane |
| `Participant` | `participant` | 7 | Conversation participant |
| `ChoreographyParticipant` | `participant` | 150 | Choreography participant band |

---

### Activities

| Signavio Stencil | BPMN 2.0 Element | Occurrences | Notes |
|------------------|------------------|-------------|-------|
| `Task` | `task` | 7,229 | Atomic activity (check `tasktype` property for Send/Receive/User/Service/etc.) |
| `CollapsedSubprocess` | `subProcess` | 385 | Collapsed subprocess |
| `Subprocess` | `subProcess` | 54 | Expanded subprocess |
| `EventSubprocess` | `subProcess` | 12 | Event-triggered subprocess (triggeredByEvent=true) |

---

### Gateways

| Signavio Stencil | BPMN 2.0 Element | Occurrences | Notes |
|------------------|------------------|-------------|-------|
| `Exclusive_Databased_Gateway` | `exclusiveGateway` | 2,505 | XOR split/join |
| `ParallelGateway` | `parallelGateway` | 600 | AND split/join |
| `AND_Gateway` | `parallelGateway` | 20 | Alias for ParallelGateway |
| `InclusiveGateway` | `inclusiveGateway` | 91 | OR split/join |
| `EventbasedGateway` | `eventBasedGateway` | 239 | Event-based decision |
| `ComplexGateway` | `complexGateway` | 5 | Complex merge/split logic |

---

### Start Events

| Signavio Stencil | BPMN 2.0 Element | Event Definition | Occurrences |
|------------------|------------------|------------------|-------------|
| `StartNoneEvent` | `startEvent` | (none) | 747 |
| `StartEvent` | `startEvent` | (none) | 36 |
| `StartMessageEvent` | `startEvent` | `messageEventDefinition` | 294 |
| `StartTimerEvent` | `startEvent` | `timerEventDefinition` | 54 |
| `StartConditionalEvent` | `startEvent` | `conditionalEventDefinition` | 12 |
| `StartSignalEvent` | `startEvent` | `signalEventDefinition` | 2 |
| `StartErrorEvent` | `startEvent` | `errorEventDefinition` | 2 |
| `StartMultipleEvent` | `startEvent` | `multipleEventDefinition` | 3 |
| `StartParallelMultipleEvent` | `startEvent` | `parallelMultipleEventDefinition` | 1 |

---

### End Events

| Signavio Stencil | BPMN 2.0 Element | Event Definition | Occurrences |
|------------------|------------------|------------------|-------------|
| `EndNoneEvent` | `endEvent` | (none) | 1,505 |
| `EndEvent` | `endEvent` | (none) | 48 |
| `EndMessageEvent` | `endEvent` | `messageEventDefinition` | 155 |
| `EndEscalationEvent` | `endEvent` | `escalationEventDefinition` | 69 |
| `EndErrorEvent` | `endEvent` | `errorEventDefinition` | 29 |
| `EndTerminateEvent` | `endEvent` | `terminateEventDefinition` | 58 |
| `EndCancelEvent` | `endEvent` | `cancelEventDefinition` | 11 |
| `EndSignalEvent` | `endEvent` | `signalEventDefinition` | 9 |

---

### Intermediate Catching Events

| Signavio Stencil | BPMN 2.0 Element | Event Definition | Occurrences |
|------------------|------------------|------------------|-------------|
| `IntermediateEvent` | `intermediateCatchEvent` | (none) | 22 |
| `IntermediateMessageEventCatching` | `intermediateCatchEvent` | `messageEventDefinition` | 789 |
| `IntermediateTimerEvent` | `intermediateCatchEvent` | `timerEventDefinition` | 352 |
| `IntermediateConditionalEvent` | `intermediateCatchEvent` | `conditionalEventDefinition` | 11 |
| `IntermediateSignalEventCatching` | `intermediateCatchEvent` | `signalEventDefinition` | 10 |
| `IntermediateLinkEventCatching` | `intermediateCatchEvent` | `linkEventDefinition` | 6 |
| `IntermediateErrorEvent` | `intermediateCatchEvent` | `errorEventDefinition` | 47 |
| `IntermediateCancelEvent` | `intermediateCatchEvent` | `cancelEventDefinition` | 3 |
| `IntermediateMultipleEventCatching` | `intermediateCatchEvent` | (multiple definitions) | 8 |
| `IntermediateParallelMultipleEventCatching` | `intermediateCatchEvent` | (parallel multiple) | 3 |
| `IntermediateCompensationEventCatching` | `intermediateCatchEvent` | `compensateEventDefinition` | 2 |

---

### Intermediate Throwing Events

| Signavio Stencil | BPMN 2.0 Element | Event Definition | Occurrences |
|------------------|------------------|------------------|-------------|
| `IntermediateMessageEventThrowing` | `intermediateThrowEvent` | `messageEventDefinition` | 301 |
| `IntermediateSignalEventThrowing` | `intermediateThrowEvent` | `signalEventDefinition` | 7 |
| `IntermediateLinkEventThrowing` | `intermediateThrowEvent` | `linkEventDefinition` | 6 |
| `IntermediateCompensationEventThrowing` | `intermediateThrowEvent` | `compensateEventDefinition` | 5 |
| `IntermediateEscalationEvent` | `intermediateThrowEvent` | `escalationEventDefinition` | 76 |
| `IntermediateEscalationEventThrowing` | `intermediateThrowEvent` | `escalationEventDefinition` | 1 |

---

### Flows / Connections

| Signavio Stencil | BPMN 2.0 Element | Occurrences | Notes |
|------------------|------------------|-------------|-------|
| `SequenceFlow` | `sequenceFlow` | 16,171 | Control flow within process |
| `MessageFlow` | `messageFlow` | 2,023 | Message exchange between pools |
| `Association_Unidirectional` | `association` | 1,788 | Directed association |
| `Association_Undirected` | `association` | 1,103 | Undirected association |
| `Association_Bidirectional` | `association` | 16 | Bidirectional association |
| `ConversationLink` | `conversationLink` | 16 | Conversation diagram link |

---

### Data Elements

| Signavio Stencil | BPMN 2.0 Element | Occurrences | Notes |
|------------------|------------------|-------------|-------|
| `DataObject` | `dataObjectReference` | 963 | Data object reference |
| `DataStore` | `dataStoreReference` | 192 | Persistent data store |
| `Message` | `message` | 86 | Message definition |
| `ITSystem` | `dataStoreReference` | 490 | Signavio-specific: maps to data store |
| `processparticipant` | `dataObjectReference` | 137 | Signavio-specific: maps to data object |

---

### Artifacts

| Signavio Stencil | BPMN 2.0 Element | Occurrences | Notes |
|------------------|------------------|-------------|-------|
| `TextAnnotation` | `textAnnotation` | 443 | Text comment |
| `Group` | `group` | 8 | Visual grouping |

---

### Choreography Elements

| Signavio Stencil | BPMN 2.0 Element | Occurrences | Notes |
|------------------|------------------|-------------|-------|
| `ChoreographyTask` | `choreographyTask` | 67 | Choreography activity |
| `ChoreographyParticipant` | `participant` | 150 | Participant band in choreography |
| `ChoreographySubprocessCollapsed` | `subChoreography` | 3 | Collapsed sub-choreography |
| `ChoreographySubprocessExpanded` | `subChoreography` | 1 | Expanded sub-choreography |

---

### Conversation Elements

| Signavio Stencil | BPMN 2.0 Element | Occurrences | Notes |
|------------------|------------------|-------------|-------|
| `Communication` | `conversation` | 8 | Conversation node |
| `Participant` | `participant` | 7 | Conversation participant |
| `ConversationLink` | `conversationLink` | 16 | Link in conversation |

---

## Notes on Special Handling

### 1. Task Types
The `Task` stencil requires checking the `tasktype` property to determine the specific BPMN task type:
- `None` -> `task`
- `Send` -> `sendTask`
- `Receive` -> `receiveTask`
- `User` -> `userTask`
- `Manual` -> `manualTask`
- `Service` -> `serviceTask`
- `Business Rule` -> `businessRuleTask`
- `Script` -> `scriptTask`

### 2. Collapsed Pools (Black-Box)
`CollapsedPool` and `CollapsedVerticalPool` represent external participants without visible internal processes. They should NOT have a `processRef` attribute in the BPMN XML.

### 3. Event Subprocesses
`EventSubprocess` maps to `subProcess` but must have `triggeredByEvent="true"` attribute.

### 4. Boundary Events
Some intermediate events may be attached to activities as boundary events. Check the parent relationship and use `boundaryEvent` instead of `intermediateCatchEvent` when attached.

### 5. Signavio-Specific Elements
- `ITSystem`: Signavio's representation of an IT system, mapped to `dataStoreReference` as the closest BPMN equivalent
- `processparticipant`: Signavio's representation of a human participant in a process, mapped to `dataObjectReference`

### 6. Multiple Event Definitions
For `StartMultipleEvent`, `IntermediateMultipleEventCatching`, and similar "Multiple" events, the actual event definitions should be extracted from the element's properties or nested structure.

---

## Missing Event Definitions

The following events are mapped but don't have explicit event definitions in `EVENT_DEFINITIONS`:

| Stencil | Suggested Event Definition |
|---------|---------------------------|
| `IntermediateMultipleEventCatching` | Multiple child definitions |
| `IntermediateParallelMultipleEventCatching` | Multiple child definitions (parallel) |

These require checking element properties or child structures to determine the actual event types.
