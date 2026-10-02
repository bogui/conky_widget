#!/bin/bash
# GPU facts from sysfs for the nouveau driver (no nvidia-smi needed).
#   gpu_info.sh name   -> "GeForce GTX 1060 3GB"
#   gpu_info.sh fan    -> "0 RPM (39%)"
#   gpu_info.sh power  -> "D0" / "D3cold"
#   gpu_info.sh temp   -> "48"

hw=""
for d in /sys/class/hwmon/hwmon*; do
    [ "$(cat "$d/name" 2>/dev/null)" = "nouveau" ] && hw="$d" && break
done

case "$1" in
    name)
        lspci -mm 2>/dev/null | awk -F'"' '/VGA|3D/ {print $6; exit}' | sed -E 's/.*\[([^]]+)\].*/\1/'
        ;;
    fan)
        [ -n "$hw" ] || { echo "n/a"; exit 0; }
        rpm=$(cat "$hw/fan1_input" 2>/dev/null || echo 0)
        pwm=$(cat "$hw/pwm1" 2>/dev/null || echo 0)
        max=$(cat "$hw/pwm1_max" 2>/dev/null || echo 255)
        [ "$max" -gt 0 ] 2>/dev/null || max=255
        if [ "$rpm" -gt 0 ] 2>/dev/null; then
            echo "${rpm} RPM ($(( pwm * 100 / max ))%)"
        else
            echo "stopped / firmware controlled"
        fi
        ;;
    power)
        cat "$hw/device/power_state" 2>/dev/null || echo "n/a"
        ;;
    temp)
        t=$(cat "$hw/temp1_input" 2>/dev/null || echo 0); echo $(( t / 1000 ))
        ;;
    *) echo "usage: $0 name|fan|power|temp" >&2; exit 2 ;;
esac
