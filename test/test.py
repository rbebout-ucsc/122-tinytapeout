# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


# 7-segment decode map (matches your Verilog decode function)
SEGMENT_MAP = {
    0b0000001: 0,
    0b1001111: 1,
    0b0010010: 2,
    0b0000110: 3,
    0b1001100: 4,
    0b0100100: 5,
    0b0100000: 6,
    0b0001111: 7,
    0b0000000: 8,
    0b0000100: 9,
    0b1111111: None,  # blank
}


async def press_button(dut, cycles=5):
    """Simulate a clean button press."""
    dut.BTN1.value = 1
    await ClockCycles(dut.CLK, cycles)
    dut.BTN1.value = 0
    await ClockCycles(dut.CLK, cycles)


def read_segments(dut):
    """Return 7-bit segment value as integer."""
    return (
        (dut.SEG_A.value.integer << 6) |
        (dut.SEG_B.value.integer << 5) |
        (dut.SEG_C.value.integer << 4) |
        (dut.SEG_D.value.integer << 3) |
        (dut.SEG_E.value.integer << 2) |
        (dut.SEG_F.value.integer << 1) |
        (dut.SEG_G.value.integer << 0)
    )


async def read_display_number(dut):
    """
    Because the display is multiplexed, we must sample both digits.
    Returns integer displayed (1–20) or None if blank.
    """
    ones = None
    tens = None

    # Sample long enough to catch both digits
    for _ in range(300):
        await ClockCycles(dut.CLK, 1)

        seg_val = read_segments(dut)

        if dut.DIG1.value == 0:  # ones active
            ones = SEGMENT_MAP.get(seg_val)
        elif dut.DIG2.value == 0:  # tens active
            tens = SEGMENT_MAP.get(seg_val)

        if ones is not None and tens is not None:
            break

    if ones is None and tens is None:
        return None

    if tens is None:
        return ones

    return tens * 10 + ones


@cocotb.test()
async def test_d20_display(dut):

    dut._log.info("Starting D20 display test")

    # 10kHz clock (100us period)
    clock = Clock(dut.CLK, 100, unit="us")
    cocotb.start_soon(clock.start())

    # --------------------------
    # RESET TEST
    # --------------------------
    dut.RST.value = 1
    dut.BTN1.value = 0
    await ClockCycles(dut.CLK, 20)
    dut.RST.value = 0
    await ClockCycles(dut.CLK, 20)

    value_after_reset = await read_display_number(dut)
    dut._log.info(f"Display after reset: {value_after_reset}")

    assert value_after_reset is None, "Reset did not clear display!"

    # --------------------------
    # START TEST (value changes)
    # --------------------------
    await press_button(dut)

    await ClockCycles(dut.CLK, 1200)
    value1 = await read_display_number(dut)

    await ClockCycles(dut.CLK, 1200)
    value2 = await read_display_number(dut)

    dut._log.info(f"Value1: {value1}, Value2: {value2}")

    assert value1 != value2, "Start did not cause value to change!"

    # --------------------------
    # STOP TEST (value freezes)
    # --------------------------
    await press_button(dut)

    stopped_value1 = await read_display_number(dut)
    await ClockCycles(dut.CLK, 1500)
    stopped_value2 = await read_display_number(dut)

    dut._log.info(f"Stopped value: {stopped_value1}")

    assert stopped_value1 == stopped_value2, "Stop did not freeze value!"

    # --------------------------
    # SEGMENT VALIDITY TEST
    # --------------------------
    assert stopped_value1 in range(1, 21), "Displayed value out of D20 range!"

    dut._log.info("All tests passed successfully.")
