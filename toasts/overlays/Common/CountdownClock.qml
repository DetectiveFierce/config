import QtQuick

// Timer-compatible clock. All visible copies of a toast share this one instance.
QtObject {
    id: clock
    property real interval: 5000
    property real remaining: interval
    property bool enabled: false
    property var holds: ({})
    readonly property bool paused: Object.keys(holds).length > 0
    readonly property bool running: enabled && !paused && interval > 0
    readonly property real progress: interval > 0 ? Math.max(0, Math.min(1, remaining / interval)) : 1
    property double lastTick: Date.now()
    signal triggered()
    onIntervalChanged: { remaining = interval; lastTick = Date.now(); }
    onRunningChanged: lastTick = Date.now()
    function advance() {
        if (!running) return;
        const now = Date.now();
        remaining = Math.max(0, remaining - Math.max(0, now - lastTick));
        lastTick = now;
        if (remaining <= 0) { enabled = false; triggered(); }
    }
    function start() {
        if (enabled) return;
        if (remaining <= 0) remaining = interval;
        lastTick = Date.now();
        enabled = true;
    }
    function stop() { advance(); enabled = false; }
    function restart() { enabled = false; remaining = interval; start(); }
    function hold(key, active) {
        advance();
        const next = Object.assign({}, holds);
        if (active) next[key] = true; else delete next[key];
        holds = next;
        lastTick = Date.now();
    }
    readonly property Timer ticker: Timer {
        interval: 16
        repeat: true
        running: clock.running
        onTriggered: clock.advance()
    }
}
