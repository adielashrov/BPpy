from bppy.model.event_selection.event_selection_strategy import \
    EventSelectionStrategy
from bppy.model.b_event import BEvent
from bppy.model.event_set import EmptyEventSet
from bppy.model.sync_statement import *
import random
from collections.abc import Iterable


class ModifierEventSelectionStrategy(EventSelectionStrategy):

    def collect_sync_statement(self, sync_statement, statement, event_set):
        if sync_statement in statement:  # should be eligible for sets
            if isinstance(statement[sync_statement], Iterable):
                event_set.update(statement[sync_statement])
            elif isinstance(statement[sync_statement], BEvent):
                event_set.add(statement[sync_statement])
            else:
                raise TypeError(
                    sync_statement + "parameter should be BEvent or iterable")

    def collect_modified_event(self, statements):
        mod_event = set()
        for statement in statements:
            self.collect_sync_statement(mod_event, statement,
                                    mod_event)
        return mod_event

    # TODO: note that we need to support/implement collect_observed_events
    #  for all event selection strategies
    def collect_declared_events(self, statements):
        requested_events = set()
        blocked_events = set()
        observed_r_events = set()
        observed_b_events = set()
        for statement in statements:
            self.collect_sync_statement(request, statement,
                                        requested_events)
            self.collect_sync_statement(block, statement,
                                        blocked_events)
            self.collect_sync_statement(o_request, statement,
                                        observed_r_events)
            self.collect_sync_statement(o_block, statement,
                                        observed_b_events)
        return requested_events, blocked_events, observed_r_events, observed_b_events

    def is_observed_requested(self, event, statement):
        if isinstance(statement.get('o_request'), BEvent):
            if isinstance(statement.get('waitFor'), BEvent):
                return statement.get('o_request') == event or statement.get(
                    'waitFor') == event
            else:
                return statement.get('o_request') == event or statement.get(
                    'waitFor', EmptyEventSet()).__contains__(event)
        else:
            if isinstance(statement.get('waitFor'), BEvent):
                return statement.get('o_request',
                                     EmptyEventSet()).__contains__(
                    event) or statement.get('waitFor') == event
            else:
                return statement.get('o_request',
                                     EmptyEventSet()).__contains__(
                    event) or statement.get('waitFor',
                                            EmptyEventSet()).__contains__(
                    event)

    def is_satisfied(self, event, statement):
        if isinstance(statement.get('request'), BEvent):
            if isinstance(statement.get('waitFor'), BEvent):
                return statement.get('request') == event or statement.get(
                    'waitFor') == event
            else:
                return statement.get('request') == event or statement.get(
                    'waitFor', EmptyEventSet()).__contains__(event)
        else:
            if isinstance(statement.get('waitFor'), BEvent):
                return statement.get('request', EmptyEventSet()).__contains__(
                    event) or statement.get('waitFor') == event
            else:
                return statement.get('request', EmptyEventSet()).__contains__(
                    event) or statement.get('waitFor',
                                            EmptyEventSet()).__contains__(
                    event)

    def selectable_events(self, statements):
        possible_events = set()
        for statement in statements:
            if 'request' in statement:  # should be eligible for sets
                if isinstance(statement['request'], Iterable):
                    possible_events.update(statement['request'])
                elif isinstance(statement['request'], BEvent):
                    possible_events.add(statement['request'])
                else:
                    raise TypeError(
                        "request parameter should be BEvent or iterable")
        for statement in statements:
            if 'block' in statement:
                if isinstance(statement.get('block'), BEvent):
                    possible_events.discard(statement.get('block'))
                else:
                    possible_events = {x for x in possible_events if
                                       x not in statement.get('block')}
        return possible_events

    def select(self, statements):
        selectable_events = self.selectable_events(statements)
        if selectable_events:
            return random.choice(tuple(selectable_events))
        else:
            return None
