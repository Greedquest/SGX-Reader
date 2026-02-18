#!/usr/bin/env python3
"""
Signavio BPMN JSON to BPMN 2.0 XML Converter

Converts SAP Signavio BPMN JSON export files to standard BPMN 2.0 XML format.
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def sanitize_id(id_str: str) -> str:
    """Sanitize an ID to be valid for xs:ID/xs:QName.

    XML IDs cannot start with a digit. If an ID starts with a digit,
    prefix it with 'id_' to make it valid.
    """
    if not id_str:
        return id_str
    if id_str[0].isdigit():
        return f'id_{id_str}'
    return id_str

# BPMN 2.0 Namespaces
NS_BPMN = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
NS_BPMNDI = 'http://www.omg.org/spec/BPMN/20100524/DI'
NS_DC = 'http://www.omg.org/spec/DD/20100524/DC'
NS_DI = 'http://www.omg.org/spec/DD/20100524/DI'
NS_XSI = 'http://www.w3.org/2001/XMLSchema-instance'

# =============================================================================
# WAYPOINT EDGE SNAPPING CONFIGURATION
# Set to True to snap waypoints to element edges (recommended for bpmn.io)
# Set to False to use original center-point waypoints (Signavio default)
# =============================================================================
SNAP_WAYPOINTS_TO_EDGES = True

# =============================================================================
# MESSAGE FLOW ROUTING CONFIGURATION
# Set to True to add intermediate waypoints for message flows crossing pools
# This creates cleaner vertical routing instead of diagonal lines
# Set to False to use original straight-line message flows
# =============================================================================
ROUTE_MESSAGE_FLOWS = True

# Pool stencil type constants
POOL_STENCILS = frozenset({'Pool', 'VerticalPool', 'CollapsedPool', 'CollapsedVerticalPool'})
COLLAPSED_POOL_STENCILS = frozenset({'CollapsedPool', 'CollapsedVerticalPool'})
HORIZONTAL_POOL_STENCILS = frozenset({'Pool', 'CollapsedPool'})
LANE_STENCILS = frozenset({'Lane', 'VerticalLane'})
ASSOCIATION_STENCILS = frozenset({'Association_Unidirectional', 'Association_Undirected', 'Association_Bidirectional'})

# Stencil to BPMN 2.0 element mapping
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

    # Signavio-specific (map to standard BPMN elements)
    'ITSystem': 'dataStoreReference',
    'processparticipant': 'dataObjectReference',  # Participant within process -> data object
}

# Event definition types based on stencil
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


@dataclass
class BPMNShape:
    """Represents a BPMN shape with its properties."""
    id: str
    stencil: str
    name: str = ''
    properties: Dict = field(default_factory=dict)
    bounds: Dict = field(default_factory=dict)
    outgoing: List[str] = field(default_factory=list)
    incoming: List[str] = field(default_factory=list)
    target: Optional[str] = None
    dockers: List[Dict] = field(default_factory=list)
    children: List['BPMNShape'] = field(default_factory=list)
    parent_id: Optional[str] = None
    process_id: Optional[str] = None
    # Absolute bounds (with parent offsets accumulated)
    absolute_bounds: Dict = field(default_factory=dict)


class XMLBuilder:
    """Simple XML builder that handles namespaces correctly."""

    def __init__(self):
        self.lines = []
        self.indent = 0

    def start_document(self):
        self.lines.append('<?xml version="1.0" encoding="UTF-8"?>')

    def _build_attrs(self, attrs: Optional[Dict[str, str]]) -> str:
        """Build attribute string for XML element."""
        if not attrs:
            return ''
        return ' ' + ' '.join(
            f'{k}="{self._escape(v)}"'
            for k, v in attrs.items()
            if v is not None
        )

    def start_element(self, name: str, attrs: Dict[str, str] = None, ns_prefix: str = None):
        tag = f'{ns_prefix}:{name}' if ns_prefix else name
        self.lines.append('  ' * self.indent + f'<{tag}{self._build_attrs(attrs)}>')
        self.indent += 1

    def end_element(self, name: str, ns_prefix: str = None):
        self.indent -= 1
        tag = f'{ns_prefix}:{name}' if ns_prefix else name
        self.lines.append('  ' * self.indent + f'</{tag}>')

    def empty_element(self, name: str, attrs: Dict[str, str] = None, ns_prefix: str = None):
        tag = f'{ns_prefix}:{name}' if ns_prefix else name
        self.lines.append('  ' * self.indent + f'<{tag}{self._build_attrs(attrs)}/>')

    def text_element(self, name: str, text: str, attrs: Dict[str, str] = None, ns_prefix: str = None):
        tag = f'{ns_prefix}:{name}' if ns_prefix else name
        self.lines.append('  ' * self.indent + f'<{tag}{self._build_attrs(attrs)}>{self._escape(text)}</{tag}>')

    def _escape(self, text: str) -> str:
        if not isinstance(text, str):
            text = str(text)
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

    def to_string(self) -> str:
        return '\n'.join(self.lines)


class SignavioBPMNConverter:
    """Converts Signavio BPMN JSON to BPMN 2.0 XML."""

    def __init__(self, json_data: Dict):
        self.json_data = json_data
        self.shapes: Dict[str, BPMNShape] = {}
        self.processes: Dict[str, List[str]] = {}
        self.pools: List[BPMNShape] = []
        self.lanes: Dict[str, List[str]] = {}
        self.sequence_flows: List[BPMNShape] = []
        self.message_flows: List[BPMNShape] = []
        self.associations: List[BPMNShape] = []
        self.data_objects: List[BPMNShape] = []
        self.messages: List[BPMNShape] = []
        self.has_collaboration = False
        self.written_flows: set = set()  # Track flows written to model for BPMNDI filtering
        self.written_shapes: set = set()  # Track shapes written to model for BPMNDI filtering
        self.valid_sequence_flows: set = set()  # Precomputed set of valid sequence flow IDs

        self._parse_shapes(json_data, None)
        self._resolve_connections()
        self._compute_valid_flows()  # Precompute which flows will be valid

    def _compute_valid_flows(self):
        """Precompute the set of valid sequence flow IDs that will actually be written."""
        for sf in self.sequence_flows:
            source_id = self._find_flow_source(sf)
            # A sequence flow is valid if it has both source and target in shapes
            if source_id and source_id in self.shapes and sf.target and sf.target in self.shapes:
                self.valid_sequence_flows.add(sf.id)

    def _parse_shapes(self, data: Dict, parent_id: Optional[str], process_id: Optional[str] = None,
                       parent_offset_x: float = 0, parent_offset_y: float = 0):
        """Recursively parse shapes from JSON data.

        Args:
            data: JSON data containing childShapes
            parent_id: ID of the parent shape
            process_id: ID of the containing process
            parent_offset_x: Accumulated X offset from all parent containers
            parent_offset_y: Accumulated Y offset from all parent containers
        """
        if 'childShapes' not in data:
            return

        for child in data['childShapes']:
            shape = self._create_shape(child, parent_id, process_id, parent_offset_x, parent_offset_y)
            if shape:
                self.shapes[shape.id] = shape
                stencil = shape.stencil

                # Calculate offset for children of this shape
                child_offset_x = parent_offset_x
                child_offset_y = parent_offset_y
                bounds = shape.bounds
                if bounds:
                    upper_left = bounds.get('upperLeft', {})
                    child_offset_x += upper_left.get('x', 0)
                    child_offset_y += upper_left.get('y', 0)

                if stencil in POOL_STENCILS:
                    self.pools.append(shape)
                    self.has_collaboration = True
                    proc_id = sanitize_id(shape.properties.get('processid', '')) or f'Process_{shape.id}'
                    shape.process_id = proc_id
                    self.processes[proc_id] = []
                    # Only parse child shapes for non-collapsed pools to avoid orphaned elements
                    if stencil not in COLLAPSED_POOL_STENCILS:
                        self._parse_shapes(child, shape.id, proc_id, child_offset_x, child_offset_y)

                elif stencil in LANE_STENCILS:
                    if process_id:
                        shape.process_id = process_id
                    self.lanes[shape.id] = []
                    self._parse_shapes(child, shape.id, process_id, child_offset_x, child_offset_y)

                elif stencil == 'SequenceFlow':
                    self.sequence_flows.append(shape)
                    self._assign_to_process(shape, process_id, add_to_elements=False)

                elif stencil == 'MessageFlow':
                    self.message_flows.append(shape)

                elif stencil in ASSOCIATION_STENCILS:
                    self.associations.append(shape)
                    self._assign_to_process(shape, process_id, add_to_elements=False)

                elif stencil in ('DataObject', 'DataStore', 'ITSystem'):
                    self.data_objects.append(shape)
                    self._assign_to_process(shape, process_id)
                    if parent_id and parent_id in self.lanes:
                        self.lanes[parent_id].append(shape.id)

                elif stencil == 'Message':
                    self.messages.append(shape)

                elif stencil in ('Subprocess', 'EventSubprocess', 'CollapsedSubprocess'):
                    self._assign_to_process(shape, process_id)
                    if parent_id and parent_id in self.lanes:
                        self.lanes[parent_id].append(shape.id)
                    self._parse_shapes(child, shape.id, process_id, child_offset_x, child_offset_y)

                else:
                    self._assign_to_process(shape, process_id)
                    if parent_id and parent_id in self.lanes:
                        self.lanes[parent_id].append(shape.id)
                    self._parse_shapes(child, shape.id, process_id, child_offset_x, child_offset_y)

    def _create_shape(self, data: Dict, parent_id: Optional[str], process_id: Optional[str],
                       parent_offset_x: float = 0, parent_offset_y: float = 0) -> Optional[BPMNShape]:
        """Create a BPMNShape from JSON data.

        Args:
            data: JSON data for the shape
            parent_id: ID of the parent shape
            process_id: ID of the containing process
            parent_offset_x: Accumulated X offset from all parent containers
            parent_offset_y: Accumulated Y offset from all parent containers
        """
        stencil = data.get('stencil', {}).get('id', '')
        if not stencil:
            return None

        resource_id = sanitize_id(data.get('resourceId', ''))
        if not resource_id:
            return None

        properties = data.get('properties', {})
        name = properties.get('name', '')
        if name:
            name = ' '.join(name.split())

        bounds = data.get('bounds', {})
        outgoing = [sanitize_id(o.get('resourceId', '')) for o in data.get('outgoing', []) if o.get('resourceId')]
        target = sanitize_id(data.get('target', {}).get('resourceId')) if data.get('target') else None
        dockers = data.get('dockers', [])

        # Calculate absolute bounds by adding parent offset
        absolute_bounds = {}
        if bounds:
            upper_left = bounds.get('upperLeft', {})
            lower_right = bounds.get('lowerRight', {})
            absolute_bounds = {
                'upperLeft': {
                    'x': upper_left.get('x', 0) + parent_offset_x,
                    'y': upper_left.get('y', 0) + parent_offset_y
                },
                'lowerRight': {
                    'x': lower_right.get('x', 0) + parent_offset_x,
                    'y': lower_right.get('y', 0) + parent_offset_y
                }
            }

        return BPMNShape(
            id=resource_id,
            stencil=stencil,
            name=name,
            properties=properties,
            bounds=bounds,
            outgoing=outgoing,
            target=target,
            dockers=dockers,
            parent_id=parent_id,
            process_id=process_id,
            absolute_bounds=absolute_bounds
        )

    def _resolve_connections(self):
        """Resolve incoming connections for all shapes."""
        for shape in self.shapes.values():
            for outgoing_id in shape.outgoing:
                if outgoing_id in self.shapes:
                    self.shapes[outgoing_id].incoming.append(shape.id)

    def _find_flow_source(self, flow: BPMNShape) -> Optional[str]:
        """Find the source element for a flow."""
        for shape_id, shape in self.shapes.items():
            if flow.id in shape.outgoing:
                return shape_id
        return None

    def _validate_flow(self, flow: BPMNShape, flow_type: str) -> Optional[Tuple[str, str]]:
        """Validate a flow has valid source and target references.

        Returns (source_ref, target_ref) tuple if valid, None otherwise.
        """
        source_ref = self._find_flow_source(flow)
        if not source_ref:
            logger.warning(f"{flow_type} {flow.id} has no source reference, skipping")
            return None
        if not flow.target:
            logger.warning(f"{flow_type} {flow.id} has no target reference, skipping")
            return None
        if source_ref not in self.shapes:
            logger.warning(f"{flow_type} {flow.id} source {source_ref} not found in shapes, skipping")
            return None
        if flow.target not in self.shapes:
            logger.warning(f"{flow_type} {flow.id} target {flow.target} not found in shapes, skipping")
            return None
        return (source_ref, flow.target)

    def _get_bounds(self, shape: BPMNShape) -> Dict:
        """Get the appropriate bounds (absolute if available, else relative)."""
        return shape.absolute_bounds or shape.bounds or {}

    def _get_center(self, bounds: Dict) -> Tuple[float, float]:
        """Calculate center point from bounds dictionary."""
        ul = bounds.get('upperLeft', {})
        lr = bounds.get('lowerRight', {})
        return (
            (ul.get('x', 0) + lr.get('x', 0)) / 2,
            (ul.get('y', 0) + lr.get('y', 0)) / 2
        )

    def _flow_belongs_to_process(self, flow: BPMNShape, process_id: str) -> bool:
        """Check if a flow belongs to a specific process."""
        if flow.process_id == process_id:
            return True
        source_id = self._find_flow_source(flow)
        if source_id and source_id in self.shapes:
            return self.shapes[source_id].process_id == process_id
        return False

    def _assign_to_process(self, shape: BPMNShape, process_id: Optional[str],
                           add_to_elements: bool = True) -> Optional[str]:
        """Assign a shape to its effective process.

        Uses hierarchy process_id or falls back to Signavio's processid property.
        Returns the effective process ID if assigned, None otherwise.
        """
        effective = process_id or sanitize_id(shape.properties.get('processid'))
        if effective and effective in self.processes:
            shape.process_id = effective
            if add_to_elements:
                self.processes[effective].append(shape.id)
            return effective
        return None

    def convert(self) -> str:
        """Convert to BPMN 2.0 XML string."""
        xml = XMLBuilder()
        xml.start_document()

        # Start definitions with all namespaces
        xml.lines.append(f'<definitions xmlns="{NS_BPMN}" '
                         f'xmlns:bpmndi="{NS_BPMNDI}" '
                         f'xmlns:dc="{NS_DC}" '
                         f'xmlns:di="{NS_DI}" '
                         f'xmlns:xsi="{NS_XSI}" '
                         f'id="Definitions_1" '
                         f'targetNamespace="http://bpmn.io/schema/bpmn" '
                         f'exporter="Signavio to BPMN Converter" '
                         f'exporterVersion="1.0">')
        xml.indent = 1

        # Add messages at definitions level
        for msg in self.messages:
            xml.empty_element('message', {'id': msg.id, 'name': msg.name or None})

        # Create collaboration if we have pools
        if self.has_collaboration:
            xml.start_element('collaboration', {'id': 'Collaboration_1'})
            for pool in self.pools:
                attrs = {'id': pool.id}
                if pool.name:
                    attrs['name'] = pool.name
                # Only add processRef for non-collapsed pools (collapsed pools represent external participants)
                if pool.process_id and pool.stencil not in COLLAPSED_POOL_STENCILS:
                    attrs['processRef'] = pool.process_id
                xml.empty_element('participant', attrs)
                self.written_shapes.add(pool.id)  # Track pool as written

            for mf in self.message_flows:
                if self._write_message_flow(xml, mf):
                    self.written_flows.add(mf.id)

            xml.end_element('collaboration')

        # Create processes
        if self.has_collaboration:
            for pool in self.pools:
                if pool.process_id and pool.stencil not in COLLAPSED_POOL_STENCILS:
                    self._write_process(xml, pool)
        else:
            self._write_default_process(xml)

        # Add diagram
        self._write_diagram(xml)

        xml.indent = 0
        xml.lines.append('</definitions>')

        return xml.to_string()

    def _write_message_flow(self, xml: XMLBuilder, mf: BPMNShape) -> bool:
        """Write a message flow element. Returns True if written successfully."""
        refs = self._validate_flow(mf, "Message flow")
        if not refs:
            return False

        attrs = {'id': mf.id, 'sourceRef': refs[0], 'targetRef': refs[1]}
        if mf.name:
            attrs['name'] = mf.name

        xml.empty_element('messageFlow', attrs)
        return True

    def _write_process(self, xml: XMLBuilder, pool: BPMNShape):
        """Write a process element for a pool.

        BPMN 2.0 XSD requires elements in this order within a process:
        1. laneSet
        2. flowElement (tasks, events, gateways, dataObjects, sequenceFlows)
        3. artifact (textAnnotation, association, group)
        """
        xml.start_element('process', {'id': pool.process_id, 'isExecutable': 'false'})

        # Add lane set if there are lanes
        pool_lanes = [s for s in self.shapes.values()
                      if s.stencil in LANE_STENCILS and s.parent_id == pool.id]

        if pool_lanes:
            xml.start_element('laneSet', {'id': f'LaneSet_{pool.id}'})
            for lane in pool_lanes:
                self._write_lane(xml, lane)
            xml.end_element('laneSet')

        # Collect process elements and separate flowElements from artifacts
        # Artifacts per XSD: textAnnotation, association, group
        process_elements = self.processes.get(pool.process_id, [])
        flow_elements = []
        artifact_shapes = []  # textAnnotation and group

        for elem_id in process_elements:
            if elem_id in self.shapes:
                shape = self.shapes[elem_id]
                if shape.stencil in ('TextAnnotation', 'Group'):
                    artifact_shapes.append(shape)
                else:
                    flow_elements.append(shape)

        # 1. Write all flowElements first (tasks, events, gateways, data objects)
        for shape in flow_elements:
            self._write_flow_element(xml, shape)

        # 2. Write sequence flows (also flowElements per XSD)
        flows_written = 0
        for sf in self.sequence_flows:
            if sf.id not in self.written_flows and self._flow_belongs_to_process(sf, pool.process_id):
                if self._write_sequence_flow(xml, sf):
                    self.written_flows.add(sf.id)
                    flows_written += 1

        logger.debug(f"Process {pool.process_id}: wrote {flows_written} sequence flows")

        # 3. Write artifacts AFTER all flowElements (textAnnotation, group, then association)
        for shape in artifact_shapes:
            self._write_artifact(xml, shape)

        for assoc in self.associations:
            if assoc.id not in self.written_flows and self._flow_belongs_to_process(assoc, pool.process_id):
                if self._write_association(xml, assoc):
                    self.written_flows.add(assoc.id)

        xml.end_element('process')

    def _write_default_process(self, xml: XMLBuilder):
        """Write a default process when there's no pool.

        BPMN 2.0 XSD requires elements in this order within a process:
        1. flowElement (tasks, events, gateways, dataObjects, sequenceFlows)
        2. artifact (textAnnotation, association, group)
        """
        xml.start_element('process', {'id': 'Process_1', 'isExecutable': 'false'})

        # Separate flowElements from artifacts
        # Artifacts per XSD: textAnnotation, association, group
        flow_elements = []
        artifact_shapes = []  # textAnnotation and group
        skip_stencils = ('BPMNDiagram', 'SequenceFlow', 'MessageFlow',
                         'Association_Unidirectional', 'Association_Undirected',
                         'Association_Bidirectional', 'Message', 'TextAnnotation', 'Group')

        for shape in self.shapes.values():
            if shape.stencil in ('TextAnnotation', 'Group'):
                artifact_shapes.append(shape)
            elif shape.stencil not in skip_stencils:
                flow_elements.append(shape)

        # 1. Write all flowElements first
        for shape in flow_elements:
            self._write_flow_element(xml, shape)

        # 2. Write sequence flows (also flowElements)
        for sf in self.sequence_flows:
            if self._write_sequence_flow(xml, sf):
                self.written_flows.add(sf.id)

        # 3. Write artifacts AFTER all flowElements (textAnnotation, group, then association)
        for shape in artifact_shapes:
            self._write_artifact(xml, shape)

        for assoc in self.associations:
            if self._write_association(xml, assoc):
                self.written_flows.add(assoc.id)

        xml.end_element('process')

    def _write_lane(self, xml: XMLBuilder, lane: BPMNShape):
        """Write a lane element."""
        attrs = {'id': lane.id}
        if lane.name:
            attrs['name'] = lane.name

        node_refs = self.lanes.get(lane.id, [])
        if node_refs:
            xml.start_element('lane', attrs)
            for node_id in node_refs:
                xml.text_element('flowNodeRef', node_id)
            xml.end_element('lane')
        else:
            xml.empty_element('lane', attrs)

        self.written_shapes.add(lane.id)  # Track lane as written

    def _write_flow_element(self, xml: XMLBuilder, shape: BPMNShape):
        """Write a flow element (task, event, gateway, etc.).

        Note: textAnnotation is an artifact, not a flowElement, and is handled
        separately by _write_text_annotation to maintain XSD element ordering.
        """
        stencil = shape.stencil
        bpmn_type = STENCIL_MAPPING.get(stencil)

        # Skip non-flowElements (artifacts like textAnnotation/group are written separately)
        if not bpmn_type or bpmn_type in ('definitions', 'participant', 'lane',
                                          'sequenceFlow', 'messageFlow', 'association',
                                          'message', 'conversationLink', 'textAnnotation', 'group'):
            return

        # Track that this shape was written to the model
        self.written_shapes.add(shape.id)

        attrs = {'id': shape.id}
        if shape.name:
            attrs['name'] = shape.name

        # Check if element has children (incoming/outgoing refs or event definitions)
        # Filter by valid sequence flows to avoid referencing skipped flows
        has_children = False
        incoming_refs = [inc for inc in shape.incoming
                        if inc in self.valid_sequence_flows]
        outgoing_refs = [out for out in shape.outgoing
                        if out in self.valid_sequence_flows]
        event_def = EVENT_DEFINITIONS.get(stencil)

        if incoming_refs or outgoing_refs or event_def:
            has_children = True

        if has_children and bpmn_type not in ('dataObjectReference', 'dataStoreReference', 'group'):
            xml.start_element(bpmn_type, attrs)

            for inc in incoming_refs:
                xml.text_element('incoming', inc)
            for out in outgoing_refs:
                xml.text_element('outgoing', out)

            if event_def:
                self._write_event_definition(xml, event_def, shape)

            xml.end_element(bpmn_type)
        else:
            xml.empty_element(bpmn_type, attrs)

    def _write_event_definition(self, xml: XMLBuilder, event_def: str, shape: BPMNShape):
        """Write an event definition element with required children/attributes.

        Handles special requirements per BPMN 2.0 XSD:
        - conditionalEventDefinition: requires <condition> child element
        - linkEventDefinition: requires 'name' attribute
        """
        def_id = f'{shape.id}_def'

        if event_def == 'conditionalEventDefinition':
            # conditionalEventDefinition requires a <condition> child element
            xml.start_element(event_def, {'id': def_id})
            # Use FormalExpression as the condition type
            condition_text = shape.properties.get('conditionexpression', '')
            xml.start_element('condition', {'xsi:type': 'tFormalExpression'})
            if condition_text:
                xml.text(condition_text)
            xml.end_element('condition')
            xml.end_element(event_def)
        elif event_def == 'linkEventDefinition':
            # linkEventDefinition requires a 'name' attribute
            link_name = shape.name or shape.properties.get('linkname', '') or shape.id
            xml.empty_element(event_def, {'id': def_id, 'name': link_name})
        else:
            # Standard event definition
            xml.empty_element(event_def, {'id': def_id})

    def _write_artifact(self, xml: XMLBuilder, shape: BPMNShape):
        """Write an artifact element (textAnnotation or group)."""
        attrs = {'id': shape.id}

        if shape.stencil == 'TextAnnotation':
            xml.start_element('textAnnotation', attrs)
            xml.text_element('text', shape.name or shape.properties.get('text', ''))
            xml.end_element('textAnnotation')
            self.written_shapes.add(shape.id)  # Track artifact as written
        elif shape.stencil == 'Group':
            # Group can have a categoryValueRef but it's optional
            xml.empty_element('group', attrs)
            self.written_shapes.add(shape.id)  # Track artifact as written

    def _write_sequence_flow(self, xml: XMLBuilder, sf: BPMNShape) -> bool:
        """Write a sequence flow element. Returns True if written successfully."""
        refs = self._validate_flow(sf, "Sequence flow")
        if not refs:
            return False

        attrs = {'id': sf.id, 'sourceRef': refs[0], 'targetRef': refs[1]}
        if sf.name:
            attrs['name'] = sf.name

        condition = sf.properties.get('conditionexpression', '')
        if condition:
            xml.start_element('sequenceFlow', attrs)
            xml.text_element('conditionExpression',
                             condition,
                             {'xsi:type': 'tFormalExpression'})
            xml.end_element('sequenceFlow')
        else:
            xml.empty_element('sequenceFlow', attrs)

        return True

    def _write_association(self, xml: XMLBuilder, assoc: BPMNShape) -> bool:
        """Write an association element. Returns True if written successfully."""
        refs = self._validate_flow(assoc, "Association")
        if not refs:
            return False

        attrs = {'id': assoc.id, 'sourceRef': refs[0], 'targetRef': refs[1]}

        if assoc.stencil == 'Association_Unidirectional':
            attrs['associationDirection'] = 'One'
        elif assoc.stencil == 'Association_Bidirectional':
            attrs['associationDirection'] = 'Both'
        else:
            attrs['associationDirection'] = 'None'

        xml.empty_element('association', attrs)
        return True

    def _write_diagram(self, xml: XMLBuilder):
        """Write BPMNDI diagram section."""
        xml.start_element('BPMNDiagram', {'id': 'BPMNDiagram_1'}, ns_prefix='bpmndi')

        plane_element = 'Collaboration_1' if self.has_collaboration else 'Process_1'
        xml.start_element('BPMNPlane', {'id': 'BPMNPlane_1', 'bpmnElement': plane_element}, ns_prefix='bpmndi')

        # Add shapes
        for shape in self.shapes.values():
            self._write_diagram_shape(xml, shape)

        # Add edges only for flows that were actually written to the model
        edges_written = 0
        edges_skipped = 0
        for flow in self.sequence_flows + self.message_flows + self.associations:
            if flow.id in self.written_flows:
                self._write_diagram_edge(xml, flow)
                edges_written += 1
            else:
                edges_skipped += 1

        logger.debug(f"BPMNDI edges: {edges_written} written, {edges_skipped} skipped (no model reference)")

        xml.end_element('BPMNPlane', ns_prefix='bpmndi')
        xml.end_element('BPMNDiagram', ns_prefix='bpmndi')

    def _write_diagram_shape(self, xml: XMLBuilder, shape: BPMNShape):
        """Write a BPMNShape to the diagram using absolute coordinates."""
        stencil = shape.stencil

        # Skip flow/edge elements (handled separately)
        if stencil in ASSOCIATION_STENCILS or stencil in ('SequenceFlow', 'MessageFlow',
                                                           'ConversationLink', 'BPMNDiagram'):
            return

        # Skip shapes that weren't written to the model (e.g., floating DataObjects without processid)
        if shape.id not in self.written_shapes:
            return

        attrs = {'id': f'{shape.id}_di', 'bpmnElement': shape.id}

        if stencil in POOL_STENCILS:
            attrs['isHorizontal'] = 'true' if stencil in HORIZONTAL_POOL_STENCILS else 'false'
        elif stencil in LANE_STENCILS:
            attrs['isHorizontal'] = 'true' if stencil == 'Lane' else 'false'

        bounds = self._get_bounds(shape)
        if bounds:
            upper_left = bounds.get('upperLeft', {})
            lower_right = bounds.get('lowerRight', {})

            x = upper_left.get('x', 0)
            y = upper_left.get('y', 0)
            width = lower_right.get('x', 100) - x
            height = lower_right.get('y', 80) - y

            xml.start_element('BPMNShape', attrs, ns_prefix='bpmndi')
            xml.empty_element('Bounds', {
                'x': str(int(x)),
                'y': str(int(y)),
                'width': str(max(int(width), 1)),
                'height': str(max(int(height), 1))
            }, ns_prefix='dc')
            xml.end_element('BPMNShape', ns_prefix='bpmndi')
        else:
            xml.empty_element('BPMNShape', attrs, ns_prefix='bpmndi')

    def _get_element_shape_type(self, shape: BPMNShape) -> str:
        """Determine the geometric shape type of a BPMN element.

        Returns: 'circle' for events, 'diamond' for gateways, 'rectangle' for others
        """
        stencil = shape.stencil.lower()
        if 'event' in stencil:
            return 'circle'
        elif 'gateway' in stencil:
            return 'diamond'
        else:
            return 'rectangle'

    def _snap_to_edge(self, center: Tuple[float, float], target_point: Tuple[float, float],
                      bounds: Dict, shape_type: str) -> Tuple[float, float]:
        """Calculate the intersection point where a line from center to target crosses the element edge.

        Args:
            center: Center point of the element (cx, cy)
            target_point: The point we're connecting to (next/previous waypoint)
            bounds: Element bounds with upperLeft and lowerRight
            shape_type: 'circle', 'diamond', or 'rectangle'

        Returns:
            The edge intersection point
        """
        cx, cy = center
        tx, ty = target_point

        # Get element dimensions
        ul = bounds.get('upperLeft', {})
        lr = bounds.get('lowerRight', {})
        x1, y1 = ul.get('x', 0), ul.get('y', 0)
        x2, y2 = lr.get('x', 0), lr.get('y', 0)
        width = x2 - x1
        height = y2 - y1

        # Direction vector from center to target
        dx = tx - cx
        dy = ty - cy

        # Avoid division by zero
        if abs(dx) < 0.001 and abs(dy) < 0.001:
            return center

        if shape_type == 'circle':
            # For circles/events, find intersection with circle
            radius = min(width, height) / 2
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > 0:
                return (cx + (dx / dist) * radius, cy + (dy / dist) * radius)
            return center

        elif shape_type == 'diamond':
            # For diamonds/gateways, find intersection with diamond edges
            # Diamond has vertices at center +/- (width/2, 0) and (0, height/2)
            hw = width / 2  # half width
            hh = height / 2  # half height

            # Normalize direction
            dist = (dx * dx + dy * dy) ** 0.5
            if dist == 0:
                return center
            ndx, ndy = dx / dist, dy / dist

            # Diamond edges form lines: |x/hw| + |y/hh| = 1
            # Scale factor to reach edge
            if abs(ndx) * hh + abs(ndy) * hw > 0:
                t = (hw * hh) / (abs(ndx) * hh + abs(ndy) * hw)
                return (cx + ndx * t, cy + ndy * t)
            return center

        else:  # rectangle
            # For rectangles/tasks, find intersection with rectangle edge
            hw = width / 2
            hh = height / 2

            # Calculate scale factors for each edge
            t_values = []

            if abs(dx) > 0.001:
                # Right edge (x = cx + hw)
                t = hw / dx if dx > 0 else -hw / dx
                if t > 0:
                    t_values.append(t)

            if abs(dy) > 0.001:
                # Bottom edge (y = cy + hh)
                t = hh / dy if dy > 0 else -hh / dy
                if t > 0:
                    t_values.append(t)

            if t_values:
                t = min(t_values)
                return (cx + dx * t, cy + dy * t)

            return center

    def _write_diagram_edge(self, xml: XMLBuilder, flow: BPMNShape):
        """Write a BPMNEdge to the diagram."""
        xml.start_element('BPMNEdge', {'id': f'{flow.id}_di', 'bpmnElement': flow.id}, ns_prefix='bpmndi')

        waypoints = self._calculate_waypoints(flow)
        for wp in waypoints:
            xml.empty_element('waypoint', {'x': str(int(wp[0])), 'y': str(int(wp[1]))}, ns_prefix='di')

        xml.end_element('BPMNEdge', ns_prefix='bpmndi')

    def _calculate_waypoints(self, flow: BPMNShape) -> List[Tuple[float, float]]:
        """Calculate waypoints for a flow from dockers and bounds.

        Signavio docker coordinate system:
        - First docker: relative to source element's upper-left corner
        - Middle dockers (if any): absolute canvas coordinates
        - Last docker: relative to target element's upper-left corner

        We use absolute_bounds to get the correct absolute positions.
        """
        waypoints = []

        try:
            source_id = self._find_flow_source(flow)
            source = self.shapes.get(source_id) if source_id else None
            target = self.shapes.get(flow.target) if flow.target else None

            dockers = flow.dockers

            # First docker: relative to source element
            if dockers and source:
                source_bounds = self._get_bounds(source)
                if source_bounds:
                    src_ul = source_bounds.get('upperLeft', {})
                    first_docker = dockers[0]
                    waypoints.append((src_ul.get('x', 0) + first_docker.get('x', 0),
                                      src_ul.get('y', 0) + first_docker.get('y', 0)))

            # Middle dockers: already in absolute canvas coordinates
            if len(dockers) > 2:
                for docker in dockers[1:-1]:
                    waypoints.append((docker.get('x', 0), docker.get('y', 0)))

            # Last docker: relative to target element
            if dockers and target:
                target_bounds = self._get_bounds(target)
                if target_bounds:
                    tgt_ul = target_bounds.get('upperLeft', {})
                    last_docker = dockers[-1]
                    waypoints.append((tgt_ul.get('x', 0) + last_docker.get('x', 0),
                                      tgt_ul.get('y', 0) + last_docker.get('y', 0)))

            # Fallback: calculate center points if not enough waypoints
            if len(waypoints) < 2:
                if source:
                    src_bounds = self._get_bounds(source)
                    if src_bounds and not waypoints:
                        waypoints.append(self._get_center(src_bounds))

                if target:
                    tgt_bounds = self._get_bounds(target)
                    if tgt_bounds:
                        waypoints.append(self._get_center(tgt_bounds))

            if len(waypoints) < 2:
                waypoints = [(0, 0), (100, 100)]

            # Apply message flow routing if enabled (before edge snapping)
            if ROUTE_MESSAGE_FLOWS and flow.stencil == 'MessageFlow' and len(waypoints) >= 2:
                waypoints = self._route_message_flow(waypoints, source, target)

            # Apply edge snapping if enabled
            if SNAP_WAYPOINTS_TO_EDGES and len(waypoints) >= 2:
                waypoints = self._apply_edge_snapping(waypoints, source, target)

        except (KeyError, TypeError) as e:
            logger.warning(f"Error calculating waypoints for flow {flow.id}: {e}, using fallback")
            waypoints = [(0, 0), (100, 100)]

        return waypoints

    def _is_pool_element(self, shape: BPMNShape) -> bool:
        """Check if an element is a pool (regular or collapsed)."""
        return shape.stencil in POOL_STENCILS

    def _apply_edge_snapping(self, waypoints: List[Tuple[float, float]],
                             source: Optional[BPMNShape],
                             target: Optional[BPMNShape]) -> List[Tuple[float, float]]:
        """Snap first and last waypoints to element edges instead of centers.

        This improves rendering in bpmn.io which expects edge connections.
        Note: Pool elements are skipped - their docker positions are preserved
        since pools are wide elements where the connection point matters.
        """
        if len(waypoints) < 2:
            return waypoints

        result = list(waypoints)

        # Snap first waypoint to source element edge (skip pools)
        if source and not self._is_pool_element(source):
            source_bounds = self._get_bounds(source)
            if source_bounds:
                center = self._get_center(source_bounds)
                next_point = waypoints[1] if len(waypoints) > 1 else waypoints[0]
                shape_type = self._get_element_shape_type(source)
                result[0] = self._snap_to_edge(center, next_point, source_bounds, shape_type)

        # Snap last waypoint to target element edge (skip pools)
        if target and not self._is_pool_element(target):
            target_bounds = self._get_bounds(target)
            if target_bounds:
                center = self._get_center(target_bounds)
                prev_point = waypoints[-2] if len(waypoints) > 1 else waypoints[-1]
                shape_type = self._get_element_shape_type(target)
                result[-1] = self._snap_to_edge(center, prev_point, target_bounds, shape_type)

        return result

    def _route_message_flow(self, waypoints: List[Tuple[float, float]],
                            source: Optional[BPMNShape],
                            target: Optional[BPMNShape]) -> List[Tuple[float, float]]:
        """Add intermediate waypoints for message flows to create cleaner vertical routing.

        Instead of diagonal lines crossing pools, this creates a path that:
        1. Goes vertically from source toward the target pool
        2. Then connects to the target

        This only applies when source and target are at significantly different Y positions.
        """
        if len(waypoints) < 2 or not source or not target:
            return waypoints

        start = waypoints[0]
        end = waypoints[-1]

        # Calculate vertical distance
        y_diff = abs(end[1] - start[1])
        x_diff = abs(end[0] - start[0])

        # Only route if there's significant vertical movement (crossing pools)
        # and the flow isn't already mostly vertical
        if y_diff < 50 or x_diff < 20:
            return waypoints

        # For message flows, create an intermediate point that makes the path cleaner
        # Go vertically from source first, then to target
        result = [start]

        # Add intermediate waypoint: same X as source, Y moving toward target
        intermediate_y = start[1] + (end[1] - start[1]) * 0.3  # 30% toward target
        result.append((start[0], intermediate_y))

        # Add another intermediate near the target's X position
        intermediate_y2 = start[1] + (end[1] - start[1]) * 0.7  # 70% toward target
        result.append((end[0], intermediate_y2))

        result.append(end)

        return result


def convert_file(input_path: Path, output_path: Path) -> bool:
    """Convert a single file."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        converter = SignavioBPMNConverter(json_data)
        xml_output = converter.convert()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_output)

        return True
    except Exception as e:
        logger.error(f"Error converting {input_path.name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Convert Signavio BPMN JSON files to BPMN 2.0 XML'
    )
    parser.add_argument('input', type=Path, help='Input JSON file or directory')
    parser.add_argument('-o', '--output', type=Path,
                        help='Output XML file or directory (default: same location with .bpmn extension)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    input_path = args.input

    if input_path.is_file():
        output_path = args.output or input_path.with_suffix('.bpmn')
        if convert_file(input_path, output_path):
            logger.info(f"Converted: {input_path} -> {output_path}")
        else:
            sys.exit(1)

    elif input_path.is_dir():
        output_dir = args.output or input_path.parent / 'bpmn_xml'
        output_dir.mkdir(exist_ok=True)

        json_files = list(input_path.glob('*.json'))
        success_count = 0
        fail_count = 0

        for json_file in json_files:
            output_file = output_dir / json_file.with_suffix('.bpmn').name
            if convert_file(json_file, output_file):
                success_count += 1
                if args.verbose:
                    logger.info(f"Converted: {json_file.name}")
            else:
                fail_count += 1

        logger.info(f"Conversion complete: {success_count} succeeded, {fail_count} failed")

    else:
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
