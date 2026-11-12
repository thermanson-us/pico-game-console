// pico_game_case.scad - two-piece snap-fit case for the Pico 2 W game console
// 2.4" Uno-shield ILI9341 + Pico 2 W (with LiPo SHIM) + LiPo battery
//
// Render a part:  set `part` below (or via the OpenSCAD Customizer), F6, then F7 to export STL.
//   "front"    - bezel with screen window (prints face-down, no supports)
//   "back"     - back cover with pin-header rails + battery box (prints floor-down)
//   "fitcheck" - the back cover's rails + battery box on a thin plate (no walls): check the pin fit
//   "all"      - both shells side by side
//
// COORDINATES (everything except the screen is given as seen from the BACK, like your photo):
//   x = right, y = up, origin = bottom-left corner of the display PCB, with the long
//   header J2 along the TOP.  z = 0 is the back surface of the display PCB, +z toward the back cover.
//
// Values marked  ** EST **  were estimated from the photo - measure and update them.

/* [Part] */
part = "all"; // ["all", "front", "back", "fitcheck"]

/* [Display board - measured] */
pcb_w = 72.3;
pcb_h = 52.6;
pcb_t = 1.6;
lcd_w = 60.0;        // display module outline
lcd_h = 42.7;

/* [Display module - measured; FRONT view, J2 header at the top] */
lcd_t = 4.3;                     // module height above PCB front surface (PCB face to glass)
lcd_off_x = 6.15;                // module left edge from PCB left edge
lcd_off_y = 5.13;                // module bottom edge from PCB bottom edge
lit_left = 10.25;                // lit area, distance in from each PCB edge
lit_right = 14.79;
lit_top = 9.35;
lit_bottom = 8.6;
panel_w = 48.96;                 // nominal 2.4" 320x240 active area - window is never smaller than this
panel_h = 36.72;
win_margin = 0.3;                // extra window size each side

/* [Display header pins - EST, back view] */
shield_tip_z = 7.6;              // MEASURED: shield pin tips above PCB back surface
j2_row = [4.0, 46.5, 50.1];      // [x start, x end, y centre] top row (J2)
j3_row = [7.0, 41.0, 2.5];       // [x start, x end, y centre] bottom row (J3)

/* [Pico 2 W + LiPo SHIM - back view] */
pico_cx = 59.9;                  // ** EST ** x of Pico centre line (from photo)
pico_y0 = pcb_h - 51.0;         // MEASURED: USB end flush with the PCB top (J2) edge
pico_gap = 2.3;                  // MEASURED: Pico sits 2.3 mm behind the display PCB back surface
pico_len = 51.0;
pico_w = 21.0;
pico_row = 17.78;                // pin-row spacing (exact, 0.7")
pico_tip_offset = 6.0;           // MEASURED: Pico pin tips stick out 6 mm further than the display's pin tips
pico_tip_z = shield_tip_z + pico_tip_offset;
shim_extra = 0;                  // ** EST ** how far the SHIM sticks out past the Pico's USB end

/* [Battery box - EST] */
batt_w = 25.0;                   // MEASURED (x: along the J2 header)
batt_l = 30.4;                   // MEASURED (y: parallel to the Pico)
batt_t = 5.0;                    // MEASURED
batt_cx = 28.9;                  // centre, back view (moved 5 mm toward the Pico)
batt_cy = 28.0;                  // moved 3 mm toward the J2 (top) edge
batt_clear = 0.6;                // clearance each side
batt_box_h = 4;                  // wall height of the battery box
batt_box_wall = 1.2;
wire_notch_w = 8;                // gap in the box wall where the battery leads exit
wire_notch_dy = -8;              // top of the opening = wire_notch_dy + wire_notch_w/2 (from box centre); runs down through the bottom corner

/* [Openings at the Pico USB end - EST] */
usb_w = 12;                      // plug overmould width
usb_z0 = -1.2;                   // USB socket faces the display PCB, centred ~1 mm behind it
usb_z1 = 3.6;
btn_dx = 0.2;                    // button opening x offset from Pico centre (rev: narrowed 3 mm on the +x side)
btn_w = 6;                       // rev: was 9
btn_z0 = pico_gap + 3.4;         // rev: moved 2 mm toward the back (was +1.4)
btn_z1 = pico_gap + 8.8;         // rev: was +6.8

/* [Header rails] */
engage = 3.0;                    // how deep pin tips go into the rails ("half-depth header")
groove_w = 0.75;                 // slot width - pins are 0.64 mm square; FDM prints slots ~0.1 mm narrow,
                                 // so this grips. Loosen to 0.8-0.85 if pins won't go in, tighten to 0.7.
pico_groove_w = 0.68;            // Pico rails a little tighter than the display rails
groove_lead = 0.5;               // lead-in chamfer at the slot mouth (each side) to guide the pins in
rail_wall = 1.2;

/* [Shell] */
wall = 2.4;                      // same as the Pico 2 case
face = 1.6;                      // front face thickness
floor_t = 1.8;                   // back cover thickness
gap = 0.5;                       // clearance around PCB / Pico
corner_r = 3.0;
min_depth = 8;

/* [Lip-and-groove snap joint - same numbers as the Pico 2 case] */
// The front shell carries an inner TONGUE (wall minus rebate) that rises joint_h above the
// joint plane (z = 0). The back shell's outer SKIRT slides down over it, so the outside stays
// flush. A continuous ridge with a ramp + flat retaining face runs round the whole tongue and
// clicks into a matching groove inside the skirt.
skirt_t = 1.2;                   // back-shell skirt thickness
skirt_clear = 0.1;               // radial clearance skirt <-> tongue
rebate = skirt_t + skirt_clear;  // = 1.3 ; tongue = wall - rebate = 1.1
joint_h = 8;                     // tongue height above the joint plane
skirt_gap = 0.3;                 // skirt stops this far short of the step on the front shell
lip_h = 0.4;                     // ridge height (radial)
lip_low = 0.6;                   // ridge extent beyond the centre line on the retaining side
lip_tip = 0.4;                   // flat tip height
lip_ramp = 0.8;                  // lead-in ramp length (0.4 rise over 0.8 = ~27 deg)
groove_bottom_clear = 0.1;       // groove edge sits this far past the retaining face (tight)
groove_top_clear = 0.25;
groove_depth_clear = 0.1;        // radial slack at the groove bottom
snap_z_from_top = 5.5;           // ridge centre line this far below the tongue tip (longer lever = gentler)
pry_w = 10; pry_h = 1.2;         // notch in the skirt edge for a screwdriver tip

$fn = 48;
e = 0.01;

// ---------------------------------------------------------------- derived
pico_y1 = pico_y0 + pico_len;                 // USB end
ix0 = min(0, pico_cx - pico_w / 2) - gap;
ix1 = max(pcb_w, pico_cx + pico_w / 2) + gap;
iy0 = min(0, pico_y0) - gap;
iy1 = max(pcb_h, pico_y1 + shim_extra) + gap;
D = max(min_depth, pico_tip_z + 1, shield_tip_z + 1, batt_t + 1);   // inner depth behind PCB
zfi = -(pcb_t + lcd_t);                        // inner surface of the front face
ox0 = ix0 - wall; oy0 = iy0 - wall;
ow = (ix1 - ix0) + 2 * wall; oh = (iy1 - iy0) + 2 * wall;

// screen module / window in BACK-view coordinates (front view is mirrored in x)
mod_x0 = pcb_w - lcd_off_x - lcd_w;
mod_cx = mod_x0 + lcd_w / 2;
mod_cy = lcd_off_y + lcd_h / 2;
lit_cx_front = (lit_left + (pcb_w - lit_right)) / 2;
win_cx = pcb_w - lit_cx_front;                       // mirrored into back-view x
win_cy = (lit_bottom + (pcb_h - lit_top)) / 2;
view_w = max(pcb_w - lit_left - lit_right, panel_w) + 2 * win_margin;
view_h = max(pcb_h - lit_top - lit_bottom, panel_h) + 2 * win_margin;

echo(str("Outer size: ", ow, " x ", oh, " x ", D + floor_t - zfi + face, " mm"));
echo(str("Inner depth behind PCB: ", D, " mm"));
echo(str("Window: ", view_w, " x ", view_h, " centred at back-view (", win_cx, ", ", win_cy, ")"));

// ---------------------------------------------------------------- helpers
module rr2d(inset) {
    r = max(corner_r - inset, 0.2);
    translate([ox0 + inset, oy0 + inset])
        offset(r = r) offset(delta = -r) square([ow - 2 * inset, oh - 2 * inset]);
}
module rr(inset, z0, z1) { translate([0, 0, z0]) linear_extrude(z1 - z0) rr2d(inset); }
module ring(in0, in1, z0, z1) { difference() { rr(in0, z0, z1); rr(in1, z0 - e, z1 + e); } }

// Continuous ridge round the tongue (same profile as the Pico 2 case): a hull of a thin
// rounded-rect slab at the ridge tip and a buried outline higher up, minus the interior, so it
// fuses 0.5 mm into the tongue and never reaches the cavity.
//   zb = z of the flat retaining face; the ramp rises toward +z (the side the skirt comes from).
module lip_ring(zb) {
    in0 = rebate - lip_h;                  // outline inset at the ridge tip
    in1 = rebate + 0.3;                    // ramp end, buried in the tongue
    ztop = zb + lip_tip + lip_ramp * (lip_h + 0.3) / lip_h;
    difference() {
        hull() {
            translate([0, 0, zb]) linear_extrude(lip_tip) rr2d(in0);
            translate([0, 0, ztop]) linear_extrude(0.01) rr2d(in1);
        }
        rr(rebate + 0.5, zb - 1, ztop + 1);
    }
}

module end_cutouts() {
    yw = (pico_y1 > pcb_h / 2) ? iy1 - 1 : oy0 - 1;     // wall at the Pico's USB end
    translate([pico_cx - usb_w / 2, yw, usb_z0]) cube([usb_w, wall + 2, usb_z1 - usb_z0]);
    translate([pico_cx + btn_dx - btn_w / 2, yw, btn_z0]) cube([btn_w, wall + 2, btn_z1 - btn_z0]);
}

// rail cross-section: u = across the rail, v = depth from the slot mouth (0) to the floor (H)
module rail_section(H, g) {
    difference() {
        translate([-(g / 2 + rail_wall), 0]) square([g + 2 * rail_wall, H]);
        polygon([[-g / 2 - groove_lead, -e], [g / 2 + groove_lead, -e],
                 [g / 2, groove_lead], [g / 2, engage],
                 [-g / 2, engage], [-g / 2, groove_lead]]);
    }
}
// rails hang from the back floor (z = top) down to just past the pin tips (z = tip - engage)
module rail_x(x0, x1, y, tip, top, g = groove_w) {
    m = tip - engage;
    translate([x0, y, m]) rotate([90, 0, 90]) linear_extrude(x1 - x0) rail_section(top - m, g);
}
module rail_y(x, y0, y1, tip, top, g = groove_w) {
    m = tip - engage;
    translate([x, y1, m]) rotate([90, 0, 0]) linear_extrude(y1 - y0) rail_section(top - m, g);
}
module rails(top) {
    rail_x(j2_row[0], j2_row[1], j2_row[2], shield_tip_z, top);    // display rails: long
    rail_x(j3_row[0], j3_row[1], j3_row[2], shield_tip_z, top);
    for (s = [-1, 1])                                               // Pico rails: 6 mm shorter
        rail_y(pico_cx + s * pico_row / 2, pico_y0 + 0.5, pico_y1 - 0.5, pico_tip_z, top, pico_groove_w);
}

module battery_box(top) {
    iw = batt_w + 2 * batt_clear; il = batt_l + 2 * batt_clear;
    translate([batt_cx, batt_cy, top - batt_box_h / 2]) difference() {
        cube([iw + 2 * batt_box_wall, il + 2 * batt_box_wall, batt_box_h], center = true);
        cube([iw, il, batt_box_h + 1], center = true);
        // wire opening: from the notch top all the way through the bottom (J3-side) wall
        let (nt = wire_notch_dy + wire_notch_w / 2, nb = -(il / 2 + batt_box_wall + 1))
            translate([iw / 2 - 1, nb, -batt_box_h]) cube([batt_box_wall + 2, nt - nb, 2 * batt_box_h]);
    }
}

// ---------------------------------------------------------------- parts
module front_shell() {
    difference() {
        union() {
            rr(0, zfi - face, 0);                              // shell body
            ring(rebate, wall + 0.2, -0.5, joint_h);           // tongue (fused 0.5 into the body)
            lip_ring(joint_h - snap_z_from_top - lip_low);     // snap ridge
        }
        rr(wall, zfi, joint_h + 1);                            // cavity
        // screen window, chamfered outward so a finger reaches the edges
        hull() {
            translate([win_cx - view_w / 2, win_cy - view_h / 2, zfi - e]) cube([view_w, view_h, e]);
            translate([win_cx - view_w / 2 - face, win_cy - view_h / 2 - face, zfi - face - e]) cube([view_w + 2 * face, view_h + 2 * face, e]);
        }
        end_cutouts();
    }
    corner_guides();
}

// L-shaped guides on the inside of the face that locate the display module
module corner_guides() {
    c = 0.3; t = 1.2; L = 5;
    for (cx = [0, 1], cy = [0, 1]) {
        x = cx ? mod_x0 + lcd_w + c : mod_x0 - c;
        y = cy ? lcd_off_y + lcd_h + c : lcd_off_y - c;
        sx = cx ? 1 : -1; sy = cy ? 1 : -1;
        translate([0, 0, zfi]) linear_extrude(1.5) {
            translate([min(x - sx * L, x + sx * t), min(y, y + sy * t)]) square([L + t, t]);
            translate([min(x, x + sx * t), min(y - sy * L, y + sy * t)]) square([t, L + t]);
        }
    }
}

module back_shell() {
    difference() {
        union() {
            rr(0, D - 0.2, D + floor_t);                       // back plate
            ring(0, wall, joint_h, D);                         // full-thickness wall above the tongue
            ring(0, skirt_t, skirt_gap, joint_h + 0.2);        // skirt that slides over the tongue
        }
        // groove inside the skirt for the ridge
        let (gz0 = joint_h - snap_z_from_top - lip_low - groove_bottom_clear,
             gz1 = joint_h - snap_z_from_top - lip_low + lip_tip + lip_ramp + groove_top_clear,
             gin = rebate - lip_h - groove_depth_clear)
            ring(gin, wall + 1, gz0, gz1);
        // pry notch in the skirt edge, middle of the J3-side wall
        translate([ox0 + ow / 2 - pry_w / 2, oy0 - 1, skirt_gap - 1]) cube([pry_w, skirt_t + 1.5, 1 + pry_h]);
        end_cutouts();
    }
    intersection() {
        rr(wall + e, 0, D + e);                                // keep internals inside the cavity
        union() { rails(D + e); battery_box(D + e); }
    }
}

// fit-check: the real back cover's rails + battery box on a thin plate, no walls.
// Same heights as the real thing, so display pins and Pico pins seat at the same time.
module fitcheck() {
    t = 1.2;
    translate([0, 0, D]) linear_extrude(t) rr2d(wall / 2);
    intersection() {
        rr(wall + e, 0, D + e);
        union() { rails(D + e); battery_box(D + e); }
    }
}

// ---------------------------------------------------------------- output (print orientation)
module front_print() { translate([0, 0, -(zfi - face)]) front_shell(); }
module back_print()  { translate([0, 0, D + floor_t]) rotate([180, 0, 0]) back_shell(); }

if (part == "front") front_print();
else if (part == "back") back_print();
else if (part == "fitcheck") translate([0, 0, D + 1.2]) rotate([180, 0, 0]) fitcheck();
else {
    front_print();
    translate([0, -(oh + 10), 0]) back_print();
}
