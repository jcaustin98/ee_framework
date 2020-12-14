# Event and messaging utilities
Many automated tasks required distributed status messages. These messages may be for real-time monitoring, compliance evidence, documentation, or problem resolution.

To address these needs I have created a set of tools that can be added to the automation process to address these messaging needs.
These loosely coupled tools include:
1) Namespace events system based on function callbacks
1) Data pipeline of event callbacks
1) API for messaging modules
    1) Slack
    1) ServiseNow - Change and Release Management
    1) Sysdig - DEVOPS metrics Monitoring 