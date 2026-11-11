import QtQuick
import QtTest
Item {
    id: root
    width: 500; height: 250
    CountdownClock { id: clock; interval: 400 }
    ToastCard {
        id: toast
        x: 50; y: 50; width: 400; height: implicitHeight
        appName: "LocalSend"; summary: "Mystic Melon wants to send 2 files"; detail: "Ma 575 Hw 5-1.jpg + 1 more · 1.1 MB"
        fileDrop: true
        actions: [{key:"reject",label:"Reject",shortcut:"esc"},{key:"accept",label:"Accept",shortcut:"enter"}]
        progress: clock.progress
        HoverHandler { onHoveredChanged: clock.hold("test-window", hovered) }
    }
    TestCase {
        name: "ToastHoverAndBorder"
        when: windowShown
        function test_pauseAndResume() {
            mouseMove(root, 1, 1);
            clock.restart();
            wait(80);
            mouseMove(toast, 100, 30);
            wait(40);
            verify(clock.paused);
            const remaining = clock.remaining;
            verify(remaining > 0 && remaining < 400);
            wait(500);
            compare(clock.remaining, remaining);
            verify(clock.enabled);
            mouseMove(root, 1, 1);
            wait(40);
            verify(!clock.paused);
            verify(clock.remaining < remaining);
            tryCompare(clock, 'remaining', 0, 1000);
            compare(clock.progress, 0);
            verify(!clock.running);
        }
        function test_borderStartsAtTopCenterClockwise() {
            clock.stop();
            clock.remaining = 300;
            wait(60);
            let image = grabImage(toast);
            // At 25% elapsed, the upper-right portion has disappeared; upper-left remains.
            const left = image.pixel(60, 1);
            const right = image.pixel(320, 1);
            verify(left.g > .7 && left.r > .4);
            verify(right.g < .3);
            clock.remaining = 0;
            wait(60);
            image = grabImage(toast);
            verify(image.pixel(60,1).g < .3);
            verify(image.pixel(398,100).g < .3);
        }
    }
}
