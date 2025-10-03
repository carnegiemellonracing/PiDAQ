# pip install smbus2
from smbus2 import SMBus
import time
import math
I2C_BUS = 1
ADDR    = 0x28        # Confirm with `i2cdetect -y 1`
# ---- MS4525DO transfer-function endpoints ----
# Set TYPE_A=True for 10–90% span; TYPE_A=False for 5–95% span
TYPE_A = True
if TYPE_A:
    C_MIN, C_MAX = 1638.3, 14745.3
else:
    C_MIN, C_MAX = 819.0, 15563.0
# Sensor range (mRo unit is typically 1 psi differential)
PMIN_PSI, PMAX_PSI = 0.0, 1.0
PSI_TO_PA = 6894.757
# Air density model:
# Option A (simple): assume ISA sea-level density
USE_SIMPLE_RHO = False
RHO_SIMPLE = 1.225  # kg/m^3 (sea level, 15°C)
# Option B (default here): estimate density from temperature + standard pressure
# rho = p / (R * T)
P_STATIC = 101325.0      # Pa (assumed static pressure)
R_AIR    = 287.05        # J/(kg·K)
# Optional: zero ΔP at startup (captures small offsets)
ZERO_SAMPLES = 50
def read_ms4525do(bus):
    # 4-byte frame
    b = bus.read_i2c_block_data(ADDR, 0x00, 4)
    status = (b[0] >> 6) & 0x03
    p_counts = ((b[0] & 0x3F) << 8) | b[1]   # 14-bit pressure
    t_counts = (b[2] << 3) | (b[3] >> 5)     # 11-bit temperature
    # Convert to psi (linear map over calibrated span)
    p_psi = (p_counts - C_MIN) * (PMAX_PSI - PMIN_PSI) / (C_MAX - C_MIN) + PMIN_PSI
    # Convert to °C per datasheet (maps 0..2047 to -50..150°C)
    t_c = (t_counts / 2047.0) * 200.0 - 50.0
    return status, p_counts, t_counts, p_psi, t_c
def pressure_to_speed(p_pa, rho):
    """
    Bernoulli: q = 0.5 * rho * V^2  =>  V = sqrt(2*q/rho)
    p_pa is differential pressure (can be signed). Use sign to indicate flow direction.
    """
    if rho <= 0:
        return float('nan'), float('nan')
    # Signed speed uses sign of ΔP; magnitude uses absolute
    mag = math.sqrt(max(0.0, 2.0 * abs(p_pa) / rho))
    signed = math.copysign(mag, p_pa)
    return signed, mag
with SMBus(I2C_BUS) as bus:
    # Optional zeroing
    offset_pa = 0.0
    if ZERO_SAMPLES > 0:
        acc = 0.0
        n = 0
        for _ in range(ZERO_SAMPLES):
            st, _, _, p_psi, _ = read_ms4525do(bus)
            if st == 0:
                acc += p_psi * PSI_TO_PA
                n += 1
            time.sleep(0.01)
        if n > 0:
            offset_pa = acc / n
        print(f"Zeroed ΔP offset: {offset_pa:.2f} Pa")
    # Stream
    while True:
        st, pc, tc, p_psi, t_c = read_ms4525do(bus)
        if st == 3:
            print("Diagnostic/fault from sensor")
            time.sleep(0.1)
            continue
        elif st == 2:
            # Stale data is okay to read; just note it
            stale_note = " (stale)"
        else:
            stale_note = ""
        # ΔP in Pa (apply offset)
        p_pa = p_psi * PSI_TO_PA - offset_pa
        # Air density
        if USE_SIMPLE_RHO:
            rho = RHO_SIMPLE
        else:
            t_k = t_c + 273.15
            rho = P_STATIC / (R_AIR * t_k)  # assumes standard pressure
        v_signed, v_mag = pressure_to_speed(p_pa, rho)
        print(
            f"ΔP={p_pa:+8.2f} Pa | T={t_c:6.2f} °C | ρ={rho:6.3f} kg/m³ | "
            f"V_signed={v_signed:6.2f} m/s | |V|={v_mag:6.2f} m/s{stale_note}"
        )
        time.sleep(0.1)

i2cdetect -y 1