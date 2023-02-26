from importlib import import_module
from inspect import getmembers, isfunction
from itertools import tee

from z3 import *


class BProgram:

    def __init__(self, bthreads=None, modifier=None,source_name=None, event_selection_strategy=None, listener=None):
        self.source_name = source_name
        self.new_bt = []
        self.bthreads = bthreads
        self.modifier = modifier
        self.event_selection_strategy = event_selection_strategy
        self.listener = listener
        self.variables = None
        self.tickets = []
        self.tickets_modifier = []

    def setup(self):
        if self.source_name:
            self.bthreads = [o[1]() for o in getmembers(import_module(self.source_name)) if
                             isfunction(o[1]) and o[1].__module__ == self.source_name]

            self.variables = dict([o for o in getmembers(import_module(self.source_name)) if
                                   isinstance(o[1], ExprRef) or isinstance(o[1], list)])

        self.new_bt = self.bthreads
        if self.modifier:
            self.tickets_modifier = [{'bt': modifier} for modifier in self.modifier]
            print("self.advance_modifier: First time")
            self.advance_modifier(None)

    # TODO: meaningful names
    def advance_bthreads(self,tickets, m):
        for l in tickets:
            if m is None or self.event_selection_strategy.is_satisfied(m, l):
                try:
                    bt = l['bt']
                    l.clear()
                    ll = bt.send(m)
                    print("Received statements from bthread: ", ll)
                    if ll is None:
                        continue
                    l.update(ll)
                    l.update({'bt': bt})
                except (KeyError, StopIteration):
                    pass

    def should_notify_modifier(self, requested_events, observed_r_events):
        requested_and_observed_r_intersect = requested_events.intersection(
            observed_r_events)
        if len(requested_and_observed_r_intersect):
            return True
        return False


    # TODO: Add here, mention to blocked events
    def advance_modifier(self, t_event=None, observed_r_events=None, observed_b_events=None):
        if self.modifier:
            for ticket in self.tickets_modifier:
                try:
                    bt = ticket['bt']
                    ll = None
                    if observed_r_events:
                        observed_events = {'observed_r_events': observed_r_events,
                                'observed_b_events': observed_b_events}
                        ll = bt.send(observed_events)
                    elif t_event is None or self.event_selection_strategy.is_satisfied(
                            t_event, ticket):
                        ll = bt.send(t_event)
                    if ll is None:
                        continue
                    ticket.clear()
                    ticket.update(ll)
                    ticket.update({'bt': bt})
                except (KeyError, StopIteration):
                    pass

    def add_bthread(self,bt):
        self.new_bt.append(bt)

    def next_event(self):
        return self.event_selection_strategy.select(self.tickets)

    def unify_tickets(self):
        unified_tickets =  self.tickets + self.tickets_modifier
        return unified_tickets

    def extract_declared_events(self):
        requested_events, blocked_events, observed_r_events, observed_b_events = self.event_selection_strategy.collect_declared_events(self.unify_tickets())
        print("requested_events:", requested_events)
        print("blocked_events:", blocked_events)
        print("observed_r_events:", observed_r_events)
        print("observed_b_events:", observed_b_events)
        return requested_events, blocked_events, observed_r_events, observed_b_events

    def extract_modified_event(self):
        m_event = self.event_selection_strategy.collect_modified_event(self.tickets_modifier)

    def should_notify_modifier(self, requested_events, observed_r_events):
        return False

    def run(self):
        if self.listener:
            self.listener.starting(b_program=self)

        # Initial setup of the b-threads - we need
        self.setup()
        # Main loop
        interrupted = False
        while not interrupted:
            # for dynamic adding new bthreads
            # Not relevant in this case
            while len(self.new_bt) > 0:
                new_tickets = [{'bt': bt} for bt in self.new_bt]
                self.new_bt.clear()
                self.advance_bthreads(new_tickets, None)
                self.tickets.extend(new_tickets)

            # Selecting an event which is requested and not blocked
            event = self.next_event()
            print(f"Selected event at sync point: {event}")
            # Finish the program if no event is selected
            if event is None:
                break

            # If the modifier thread is interested in the currently
            # requested events
            modified = False
            if self.modifier:
                requested_events, blocked_events, observed_r_events, observed_b_events = self.extract_declared_events()
                # TODO: Handle case where we are in a regular
                #  synchronization point - there is no modify declaration.
                if self.should_notify_modifier(requested_events,
                                               observed_r_events):
                    self.advance_modifier(observed_r_events = observed_r_events,
                                          observed_b_events = observed_b_events)
                    event = self.extract_modified_event()
                    # Finish the program if modifier returned an empty set
                    if event is None:
                        print("Modifier scenario returned an empty set.")
                        break
                    else:
                        modified = True

            # notify the listener
            if self.listener:
                interrupted = self.listener.event_selected(b_program=self,
                                                           event=event)

            # We attempt to promote the modifier thread if the
            # event was not modified at sync point
            if self.modifier:
                if modified:
                    self.advance_modifier(t_event=None)
                else:
                    print(f"advancing modifier with event:{event}")
                    self.advance_modifier(t_event=event)

            self.advance_bthreads(self.tickets, event)

        if self.listener:
            self.listener.ended(b_program=self)