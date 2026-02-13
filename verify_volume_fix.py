def normalize_volume(volume, step):
    import math
    if step <= 0: return volume
    # Round to nearest step
    vol = round(volume / step) * step
    
    # Fix float precision issues (e.g. 0.12000000000000001 -> 0.12)
    if step < 1:
        # Calculate decimals based on step (0.01 -> 2, 0.001 -> 3)
        decimals = int(round(-math.log10(step), 0))
        vol = round(vol, decimals)
    
    return vol

# Test cases from logs
test_volumes = [
    0.11843087002555763,
    0.12937016797590586,
    0.13011046488933992,
    0.12593951820096116,
    0.1276989441745713
]

step = 0.01 # Standard for synthetics usually

print(f"Testing volume normalization with step {step}:")
for v in test_volumes:
    norm = normalize_volume(v, step)
    print(f"  Original: {v} -> Normalized: {norm}")

# Test with other steps
step2 = 0.1
print(f"\nTesting with step {step2}:")
for v in test_volumes:
    norm = normalize_volume(v, step2)
    print(f"  Original: {v} -> Normalized: {norm}")
