# ME-405-term-project
# AUTOMATED IR NERF TURRET 

## Introduction
This projects goal was to design, construct and program a automated nerf turret that is capable of shooting a person 16 feet awya using an IR camera for signal detection. The firing conditions for this turret are a predetermined set of "deuling rules" specified in the following steps:

1. The turret must start facing away from the intended target
2. The turret will then roate 180 degrees to face the general area of the intended target
3. The intended target will have 5 seconds to move around. by this point your turret is allowed to fire.
4. After 5 seconds from the start of the duel the intended target must stand still for atleast 10 seconds.
5. The turret can fire any amount of shot sduring either step 3 or 4. The scoring is based on if the opposing targets turret hit first, how many shots hit, and how many shots missed. 

The turret is intended to be used exclusivley for the ME 405 Learn by Dueling Competition by the students who designed and programmed it and another other ME 405 students who wanted to try using the turret. 

---

# Turret Design

## Hardware Design
Our hardware design philisophy is based almost entirley around being compatible with the NERF gun we chose. For our turret we chose the NERF Ultra Select 2. An electronic firing mechanism and flywheel firing system where desirable as it made actuating the gun a pre-packaged operation. The only difficulty was the size of the gun made it difficult to design a fixture for. The design is outlined in [our CAD folder](https://github.com/rmevorac/ME-405-term-project/tree/main/SLDWRK). The 3 important design attributes of our final turret design are the yaw axis, the pitch axis, and the fixture. The yaw axis is composed of a lazy susan that sits on 4 legs conencting to the bottom half, and a pivot with a shaft coming through the middle of bearing downards which sits on the top. The yaw axis is driven by the 405 kot motors through a 400mm belt and a 3.75:1 torque pulley ratio. The pivot which composes the pitch axis as was designed around a set of 30mm bearing found within the ME 405 lab. The pivot piece which the large black 3D printed object, was printed with the assistance and guidance of Thomas Mcklay Taylor, another ME 405 student. The pitch axis is driven by a worm gear to spline gear system with an approximate gear ratio of 11:1 as to not be easily backdrivable. This drives a winch system that raises and lowers the gun. The pivot is attached to the final component set which is known as the gun clamp. This is a two piece mechanism which both acts as the shaft for which the gun pivots around and the mechanism which keeps the gun secured to the turret. Photos of the general design are provided below:

## Software Design

Our software design is provided in great detail on our doxygen gituhub.io page for this project, please refer to the link below for more detailed information:


---

# Project Outcome

## Performance

## What We Learned


---

# Original Description

We are intending to make a 2 axis turret equipped with an electronic nerf launcher. The goal is to use a medium sized motor likely one of the tub motors for horizontal panning and either a more powerful motor we purchased online or a dual tub motor gearbox. We are likely going to 3D print most of the superstructural pieces and manufacture components like the trigger mechanism. The goal is to get the gun to land the first shot. We are confident on our electric gun choice but unsure on the motor selection.

Motors: 
Pitch Motor : Tub motor 
Yaw Motor: 1 – 2 Tub motors

Drive System: 
Pitch: Likely a single gear step (not including gearbox on motors) in the range of 2:1 to 4:1
Yaw: Also a single gear step in the range of 2:1 to 5:1 or utilize a two motor gearbox

Nerf Gun:
Vendor: Amazon
Model: Nerf Ultra Select
https://www.amazon.com/NERF-F0958-NER-Ultra-Select/dp/B08SYD2685?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&psc=1&smid=ATVPDKIKX0DER 

Data sheet for Nerf Gun: https://icecat.biz/p/nerf/f0958u50/ultra-toy+weapons-5010993855285-select-89523906.html

Data sheet for Adafruit MLX90640 IR Thermal Camera: https://learn.adafruit.com/adafruit-mlx90640-ir-thermal-camera/downloads

Trigger System:
Electronic Trigger System


Total Cost:
Nerf Ultra Select Gun - $51


Task Diagram:
![TDV1](https://user-images.githubusercontent.com/56085595/222069197-0ed7baf2-8def-4cf4-a6a4-fca194ef7bc9.jpg)

FSM:
![FSMV1](https://user-images.githubusercontent.com/56085595/222069215-9171dbce-964f-4f7f-9de4-17c2358491e7.jpg)


