// Set screw symbol for the Cullenect labels of FusionGridfinityGenerator (fork Eifel-Joe), MIT License, see LICENSE.
// Own work of this fork. The thread, the point and the driver shapes are Cullenect's modules
// (Cullenect-Labels by CullenJWebb, MIT, ../cullenect), drawn the way cullenect_label_generate draws a screw:
// centered on where a head would be, the shaft to the left.
//
// A set screw has no head, its driver is in its end. The end is drawn as a disc beside the thread, a gap apart,
// as a view onto it, with the driver cut out at a smaller scale so a rim stays around it.

use <../cullenect/Cullenect.scad>

setScrewDriverX = 6;      // diameter of the end face, Cullenect's driverX
setScrewGap = 1;          // between the end face and the thread
setScrewDriverScale = 0.7; // of Cullenect's driver shapes, they nearly fill a 6 mm disc
setScrewLayer = 0.2;      // Cullenect's layer

module set_screw(shaft = "machine", driver = "hex", security = false) {
    union() {
        difference() {
            cylinder(h = setScrewLayer, d = setScrewDriverX, center = true);
            scale([setScrewDriverScale, setScrewDriverScale, 1])
                cullenect_driver(driver = driver);
        }
        if (security)
            scale([setScrewDriverScale, setScrewDriverScale, 1])
                cullenect_driver(driver = "security");
        // Cullenect's shaft starts at the edge of the head, -driverX / 2
        translate([-setScrewGap, 0, 0])
            cullenect_shaft(shaft = shaft, threads = "full");
    }
}
