<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

The goal of this design is to have the user roll a d20 dice by clicking an external button. The program runs when a user clicks the roll button, using a LFSR to grab a random number. The display will delay for half a second before displaying the value, and the user can roll again to generate a new value. The brief delay between rolls is to avoid any visual glitches in the display. There is also an external reset button for the user to clear the display. I built this program by prompting an LLM (started with chatGPT, migrated to Claude for improved functionality) to build out the modules, tweaking them until they were fully functional. I also used Claude to set up the cocotb testbench that tests the functionality of the design in the context of TinyTapeout. This tests that rolling generates a valid number, that the numbers are different between rolls, that rolls are in the valid range of 1-20, and that reset clears the display.

## How to test

To test this project, you can run the Wokwi simulation here: https://wokwi.com/projects/457499964475678721

