import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.Common
import qs.Services
import qs.Widgets

PanelWindow {
    id: root
    property var modelData
    property bool shouldBeVisible: ToastService.toastVisible
    property bool expanded: false
    WlrLayershell.namespace: "dms:toast"
    screen: modelData
    visible: shouldBeVisible || exitDelay.running
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.exclusiveZone: -1
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    anchors.top: true
    anchors.left: true
    implicitWidth: 410
    implicitHeight: design.implicitHeight + 10
    WlrLayershell.margins.left: Math.max(0, Math.min((modelData?.width ?? 1920)-implicitWidth, BarWidgetService.toastCenter(modelData)-implicitWidth/2))
    WlrLayershell.margins.top: 1
    Connections {
        target: ToastService
        function onToastVisibleChanged() {
            if (ToastService.toastVisible) { exitDelay.stop(); root.shouldBeVisible = true; }
            else { root.shouldBeVisible = false; exitDelay.restart(); }
        }
        function onResetToastState() { root.expanded = false; ToastService.holdToast("details", false); }
    }
    Timer { id: exitDelay; interval: 280 }
    Item {
        id: surface
        x: 5
        y: root.shouldBeVisible ? 5 : -height-20
        width: 400
        height: design.implicitHeight
        Behavior on y { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
        HoverHandler {
            id: hover
            onHoveredChanged: ToastService.holdToast(root.modelData.name, hovered)
        }
        Component.onDestruction: ToastService.holdToast(root.modelData?.name ?? "", false)
        ToastCard {
            id: design
            anchors.fill: parent
            appName: ToastService.currentCategory.toLowerCase().indexOf("bluetooth") >= 0 ? "Bluetooth" : "System"
            summary: ToastService.currentMessage
            detail: ToastService.currentDetails + (ToastService.currentCommand ? "\n" + ToastService.currentCommand : "")
            expanded: root.expanded
            progress: ToastService.countdownProgress
            actions: ToastService.hasDetails ? [{key:"details",label:root.expanded ? "Less" : "Details"},{key:"copy",label:"Copy"}] : []
            onActionInvoked: key => {
                if (key === "details") {
                    root.expanded = !root.expanded;
                    ToastService.holdToast("details", root.expanded);
                } else if (key === "copy") {
                    Quickshell.execDetached(["wl-copy", ToastService.currentDetails + "\n" + ToastService.currentCommand]);
                }
            }
        }
    }
    mask: Region { item: surface }
}
