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

    def setup(self):
        if self.source_name:
            self.bthreads = [o[1]() for o in getmembers(import_module(self.source_name)) if
                             isfunction(o[1]) and o[1].__module__ == self.source_name]

            self.variables = dict([o for o in getmembers(import_module(self.source_name)) if
                                   isinstance(o[1], ExprRef) or isinstance(o[1], list)])

        self.new_bt = self.bthreads

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

    def add_bthread(self,bt):
        self.new_bt.append(bt)

    def next_event(self):
        return self.event_selection_strategy.select(self.tickets)

    def check_if_event_should_be_modified(self, observed_r_events=None,
                                          observed_b_events=None):
        return True

    def extract_declared_events(self):
        requested_events, blocked_events, observed_r_events, observed_b_events = self.event_selection_strategy.collect_declared_events(self.tickets)
        print("requested_events:", requested_events)
        print("blocked_events:", blocked_events)
        print("observed_r_events:", observed_r_events)
        print("observed_b_events:", observed_b_events)
        return requested_events, blocked_events, observed_r_events, observed_b_events

    def should_notify_modifier(self, requested_events, observed_r_events):
        requested_and_observed_r_intersect = requested_events.intersection(observed_r_events)
        if len(requested_and_observed_r_intersect):
            return True
        return False

    #TODO: continue here
    def advance_modifier(self,observed_r_events):
        pass

    def run(self):
        if self.listener:
            self.listener.starting(b_program=self)

        self.setup()
        # Main loop
        interrupted = False
        while not interrupted:
            # for dynamic adding new bthreads
            while len(self.new_bt)>0:
                new_tickets = [{'bt': bt} for bt in self.new_bt]
                self.new_bt.clear()
                self.advance_bthreads(new_tickets,None)
                self.tickets.extend(new_tickets)

            # Selecting an event which is requested and not blocked
            event = self.next_event()
            # Finish the program if no event is selected
            if event is None:
                break

            # Check if there is a modifier b_thread
            if self.modifier:
                requested_events, blocked_events, observed_r_events, observed_b_events = self.extract_declared_events()
                if self.should_notify_modifier(requested_events, observed_r_events):
                    self.advance_modifier(observed_r_events)

            # notify the listener
            if self.listener:
                interrupted = self.listener.event_selected(b_program=self, event=event)

            self.advance_bthreads(self.tickets,event)


        if self.listener:
            self.listener.ended(b_program=self)
