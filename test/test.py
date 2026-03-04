# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

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
    dut.ui_in.value = dut.ui_in.value.to_unsigned() | 0b00000010
    await ClockCycles(dut.clk, cycles)
    dut.ui_in.value = dut.ui_in.value.to_unsigned() & 0b11111101
    await ClockCycles(dut.clk, cycles)

def read_segments(dut):
    """Return 7-bit segment value from uo_out bits 0-6, or None if X/Z."""
    try:
        val = dut.uo_out.value.to_unsigned()
    except ValueError:
        return None
    return (
        ((val >> 0) & 1) << 6 |
        ((val >> 1) & 1) << 5 |
        ((val >> 2) & 1) << 4 |
        ((val >> 3) & 1) << 3 |
        ((val >> 4) & 1) << 2 |
        ((val >> 5) & 1) << 1 |
        ((val >> 6) & 1) << 0
    )

async def read_display_number(dut):
    """
    Because the display is multiplexed, we must sample both digits.
    Returns integer displayed (1-20) or None if blank.
    """
    ones = None
    tens = None
    for _ in range(300):
        await ClockCycles(dut.clk, 1)
        seg_val = read_segments(dut)
        if seg_val is None:
            continue
        try:
            uio_val = dut.uio_out.value.to_unsigned()
        except ValueError:
            continue
        dig1 = (uio_val >> 0) & 1
        dig2 = (uio_val >> 1) & 1
        if dig1 == 0:
            ones = SEGMENT_MAP.get(seg_val)
        elif dig2 == 0:
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

    # Initialize all inputs before clock starts
    dut.rst_n.value = 1
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    # 10kHz clock (100us period)
    clock = Clock(dut.clk, 100, unit="us")
    cocotb.start_soon(clock.start())

    # --------------------------
    # RESET TEST
    # --------------------------
    dut.ui_in.value = 0b00000001  # RST = bit 0 high
    await ClockCycles(dut.clk, 20)
    dut.ui_in.value = 0b00000000  # RST low
    await ClockCycles(dut.clk, 20)

    value_after_reset = await read_display_number(dut)
    dut._log.info(f"Display after reset: {value_after_reset}")
    assert value_after_reset is None, "Reset did not clear display!"

    # --------------------------
    # START TEST (value changes)
    # --------------------------
    await press_button(dut)
    await ClockCycles(dut.clk, 1200)
    value1 = await read_display_number(dut)
    await ClockCycles(dut.clk, 1200)
    value2 = await read_display_number(dut)
    dut._log.info(f"Value1: {value1}, Value2: {value2}")
    assert value1 != value2, "Start did not cause value to change!"

    # --------------------------
    # STOP TEST (value freezes)
    # --------------------------
    await press_button(dut)
    stopped_value1 = await read_display_number(dut)
    await ClockCycles(dut.clk, 1500)
    stopped_value2 = await read_display_number(dut)
    dut._log.info(f"Stopped value: {stopped_value1}")
    assert stopped_value1 == stopped_value2, "Stop did not freeze value!"

    # --------------------------
    # SEGMENT VALIDITY TEST
    # --------------------------
    assert stopped_value1 in range(1, 21), "Displayed value out of D20 range!"
    dut._log.info("All tests passed successfully.")