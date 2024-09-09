# Mock version of automationhat

class MockPower:
    def on(self):
        print("Power is ON")

    def off(self):
        print("Power is OFF")

class MockRelay:
    def __init__(self):
        self.on = MockPower().on
        self.off = MockPower().off


class MockRelayGroup:
    def __init__(self):
        self.one = MockRelay()

class MockAutomationHat:
    def __init__(self):
        self.relay = MockRelayGroup()
        
automationhat = MockAutomationHat()
import sys
sys.modules[__name__] = automationhat
# Test:
# import automationhat
# automationhat.relay.one.on()
