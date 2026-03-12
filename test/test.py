# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
import random

# Derived from display_driver.v decode() with direct bit assignment in top_level.v:
#   uo_out[i] = seg_wire[i] — no reversal, map is decode() output directly.
# Segments are active-low so uo_out & 0x7F matches decode() table directly.
SEGMENT_MAP = {
    0b0000000: 8,
    0b0000001: 0,
    0b0000100: 9,
    0b0000110: 3,
    0b0001111: 7,
    0b0010010: 2,
    0b0100000: 6,
    0b0100100: 5,
    0b1001100: 4,
    0b1001111: 1,
    0b1111111: None,  # blank
}

# Digit select from display_driver digits_wire -> uio_out directly:
#   digits=2'b01: uio_out[0]=1, uio_out[1]=0 -> ones active
#   digits=2'b10: uio_out[0]=0, uio_out[1]=1 -> tens active

def safe_int(signal, default=None):
    try:
        return int(signal.value)
    except ValueError:
        return default

# -------------------------------------------------------------------
# Signal drivers
# rst_n is the hardware reset — active low, no debounce needed
# ui_in[0] is the roll button — debounced in hardware (DEBOUNCE_CYCLES=500)
# -------------------------------------------------------------------
async def do_reset(dut):
    """Assert rst_n low briefly to reset all registers."""
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 100)

async def do_start(dut):
    """Press roll button with random pre-delay for LFSR variance."""
    await ClockCycles(dut.clk, random.randint(0, 5000))
    hold = 600 + random.randint(0, 500)
    dut.ui_in.value = 0b00000001  # ui_in[0] = roll button
    await ClockCycles(dut.clk, hold)
    dut.ui_in.value = 0b00000000
    await ClockCycles(dut.clk, 1200)  # wait for debounce release to settle

async def wait_for_active(dut, timeout_cycles=30000):
    """Wait until display shows a non-blank segment on either digit."""
    for _ in range(timeout_cycles):
        await ClockCycles(dut.clk, 1)
        uio_val = safe_int(dut.uio_out)
        uo_val  = safe_int(dut.uo_out)
        if uio_val is None or uo_val is None:
            continue
        ones_active = (uio_val >> 0) & 1
        tens_active = (uio_val >> 1) & 1
        seg = uo_val & 0x7F
        if (ones_active or tens_active) and seg != 0x7F:
            return True
    return False

async def init(dut):
    """Initialise signals and assert rst_n at startup."""
    dut.rst_n.value  = 0
    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    clock = Clock(dut.clk, 20, unit="us")
    cocotb.start_soon(clock.start())
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value  = 1
    await ClockCycles(dut.clk, 100)

# -------------------------------------------------------------------
# Display reading
# -------------------------------------------------------------------
async def sample_one_mux_cycle(dut, timeout=200):
    """
    Capture one complete ones->tens mux cycle, same-cycle seg+digit read.
    Returns (ones, tens) or None on timeout.
    """
    ones = None
    tens = None
    saw_ones = False

    for _ in range(timeout):
        await ClockCycles(dut.clk, 1)
        uio_val = safe_int(dut.uio_out)
        if uio_val is None:
            continue
        uo_val = safe_int(dut.uo_out)
        if uo_val is None:
            continue

        ones_active = (uio_val >> 0) & 1  # 1 = ones digit active
        tens_active = (uio_val >> 1) & 1  # 1 = tens digit active
        seg = uo_val & 0x7F

        if ones_active and not saw_ones:
            ones = SEGMENT_MAP.get(seg)
            saw_ones = True
        elif tens_active and saw_ones:
            tens = SEGMENT_MAP.get(seg)
            return (ones, tens)

    return None

def digits_to_number(ones, tens):
    """Convert (ones, tens) to integer. None if fully blank."""
    if ones is None and tens is None:
        return None
    if tens is None or tens == 0:
        return ones
    return tens * 10 + ones

async def read_display_number(dut, required_stable=3, timeout_cycles=8000):
    """Read display requiring required_stable consecutive cycles to agree."""
    last = "unset"
    streak = 0
    cycles_used = 0
    while cycles_used < timeout_cycles:
        result = await sample_one_mux_cycle(dut)
        cycles_used += 200
        if result is None:
            streak = 0
            last = "unset"
            continue
        number = digits_to_number(*result)
        if number == last:
            streak += 1
            if streak >= required_stable:
                return number
        else:
            last = number
            streak = 1
    return None

async def read_display_blank(dut, required_stable=4, timeout_cycles=6000):
    """Confirm display blank across required_stable consecutive cycles."""
    streak = 0
    cycles_used = 0
    while cycles_used < timeout_cycles:
        result = await sample_one_mux_cycle(dut)
        cycles_used += 200
        if result is None:
            streak = 0
            continue
        number = digits_to_number(*result)
        if number is not None:
            return False
        streak += 1
        if streak >= required_stable:
            return True
    return True

# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

@cocotb.test()
async def test_roll_produces_valid_value(dut):
    """After a roll, display should show a valid D20 number (1-20)."""
    dut._log.info("TEST: roll produces valid D20 value")
    await init(dut)
    await do_reset(dut)
    await do_start(dut)
    active = await wait_for_active(dut)
    assert active, "Display never became active after roll"
    value = await read_display_number(dut)
    dut._log.info(f"Rolled value: {value}")
    assert value is not None, "Display is blank after roll — expected a value"
    assert 1 <= value <= 20, f"Rolled value {value} is outside D20 range 1-20"
    dut._log.info(f"PASS: rolled value {value} is a valid D20 result")


@cocotb.test()
async def test_consecutive_rolls_differ(dut):
    """Roll 5 times and verify not all results are identical."""
    dut._log.info("TEST: consecutive rolls produce different values")
    await init(dut)
    await do_reset(dut)
    results = []
    for i in range(5):
        await do_start(dut)
        active = await wait_for_active(dut)
        assert active, f"Display never became active on roll {i+1}"
        value = await read_display_number(dut)
        dut._log.info(f"Roll {i+1}: {value}")
        assert value is not None, f"Display blank on roll {i+1}"
        assert 1 <= value <= 20, f"Roll {i+1} value {value} out of range"
        results.append(value)
    unique = len(set(results))
    dut._log.info(f"Unique values across 5 rolls: {unique} — {results}")
    assert unique > 1, f"All 5 rolls returned {results[0]} — LFSR may be stuck"
    dut._log.info("PASS: consecutive rolls produce varied results")


@cocotb.test()
async def test_display_range_validity(dut):
    """Roll 10 times and verify every result is in range 1-20."""
    dut._log.info("TEST: all rolled values in range 1-20")
    await init(dut)
    await do_reset(dut)
    for i in range(10):
        await do_start(dut)
        active = await wait_for_active(dut)
        assert active, f"Display never became active on roll {i+1}"
        value = await read_display_number(dut)
        dut._log.info(f"Roll {i+1}: {value}")
        assert value is not None, f"Display blank on roll {i+1}"
        assert 1 <= value <= 20, f"Roll {i+1} returned {value}, out of range 1-20"
    dut._log.info("PASS: all 10 rolls in valid D20 range")


@cocotb.test()
async def test_reset_clears_display(dut):
    """Reset should blank the display both before and after a roll."""
    dut._log.info("TEST: reset clears display")
    await init(dut)

    # Fresh reset — should be blank
    await do_reset(dut)
    await ClockCycles(dut.clk, 100)
    is_blank = await read_display_blank(dut)
    dut._log.info(f"Blank after initial reset: {is_blank}")
    assert is_blank, "Expected blank display after initial reset"

    # Roll then reset — should blank again
    await do_start(dut)
    active = await wait_for_active(dut)
    assert active, "Display never became active after roll"
    value = await read_display_number(dut)
    dut._log.info(f"Value before reset: {value}")
    assert value is not None, "Display blank before second reset — roll may have failed"
    await do_reset(dut)
    await ClockCycles(dut.clk, 100)
    is_blank = await read_display_blank(dut)
    dut._log.info(f"Blank after reset post-roll: {is_blank}")
    assert is_blank, "Expected blank display after reset post-roll"
    dut._log.info("PASS: reset clears display in both cases")
