import QtQuick

Canvas {
    id: border
    property real progress: 1
    property real thickness: 3
    property real cornerRadius: 8
    property color accent: "#a6e22e"
    antialiasing: true
    onProgressChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        if (progress <= 0 || width < 4 || height < 4) return;
        const inset = thickness / 2;
        const l = inset, t = inset, r = width-inset, b = height-inset;
        const rad = Math.min(cornerRadius-inset, (r-l)/2, (b-t)/2);
        const mid = width/2;
        const pieces = [];
        function line(x1,y1,x2,y2) { pieces.push({len: Math.hypot(x2-x1,y2-y1),x1:x1,y1:y1,x2:x2,y2:y2}); }
        function arc(cx,cy,a1,a2) { pieces.push({len:rad*(a2-a1),cx:cx,cy:cy,a1:a1,a2:a2}); }
        // Clockwise path begins at the midpoint of the top edge.
        line(mid,t,r-rad,t); arc(r-rad,t+rad,-Math.PI/2,0);
        line(r,t+rad,r,b-rad); arc(r-rad,b-rad,0,Math.PI/2);
        line(r-rad,b,l+rad,b); arc(l+rad,b-rad,Math.PI/2,Math.PI);
        line(l,b-rad,l,t+rad); arc(l+rad,t+rad,Math.PI,Math.PI*1.5);
        line(l+rad,t,mid,t);
        const perimeter = pieces.reduce((sum, piece) => sum+piece.len,0);
        let skip = (1-Math.max(0,Math.min(1,progress))) * perimeter;
        ctx.beginPath();
        let begun = false;
        for (const piece of pieces) {
            if (skip >= piece.len) { skip -= piece.len; continue; }
            const f = skip / piece.len;
            if (piece.cx !== undefined) {
                const angle = piece.a1+(piece.a2-piece.a1)*f;
                if (!begun) ctx.moveTo(piece.cx+rad*Math.cos(angle),piece.cy+rad*Math.sin(angle));
                ctx.arc(piece.cx,piece.cy,rad,angle,piece.a2,false);
            } else {
                if (!begun) ctx.moveTo(piece.x1+(piece.x2-piece.x1)*f,piece.y1+(piece.y2-piece.y1)*f);
                ctx.lineTo(piece.x2,piece.y2);
            }
            begun = true;
            skip = 0;
        }
        ctx.strokeStyle = accent;
        ctx.lineWidth = thickness;
        ctx.lineCap = "butt";
        ctx.stroke();
    }
}
