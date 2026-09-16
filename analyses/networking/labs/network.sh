#!/usr/bin/env bash
# Build only the isolated topology described in chapter 8.
set -euo pipefail

state_dir=/run/hdw-network-tutorial
namespaces=(hdw-c hdw-r hdw-s)

fail() { printf '%s\n' "$*" >&2; exit 1; }

exists() { ip netns list | awk '{print $1}' | grep -Fxq -- "$1"; }

cleanup() {
    local ns pid
    [[ -d "$state_dir" ]] || return 0
    for ns in "${namespaces[@]}"; do
        [[ -f "$state_dir/$ns" ]] || continue
        if exists "$ns"; then
            # Stop only processes in namespaces recorded as created by this lab.
            while read -r pid; do
                [[ -n "$pid" ]] && kill -TERM "$pid" 2>/dev/null || true
            done < <(ip netns pids "$ns")
            ip netns delete "$ns"
        fi
        rm -f -- "$state_dir/$ns"
    done
    rmdir -- "$state_dir"
}

[[ $(uname -s) == Linux ]] || fail "Run this lab inside Linux."
[[ $EUID -eq 0 ]] || fail "Run with sudo bash labs/network.sh up|down."
command -v ip >/dev/null || fail "Install iproute2 first."

case "${1:-}" in
    up)
        [[ ! -e "$state_dir" ]] || fail "Lab state already exists. Run down before rebuilding."
        for ns in "${namespaces[@]}"; do
            ! exists "$ns" || fail "Namespace $ns already exists; refusing to change it."
        done
        umask 077
        mkdir -- "$state_dir"
        trap cleanup EXIT
        trap 'exit 130' INT
        trap 'exit 143' TERM
        for ns in "${namespaces[@]}"; do
            ip netns add "$ns"
            touch "$state_dir/$ns"
            ip -n "$ns" link set lo up
        done

        ip -n hdw-c link add eth0 type veth peer name left netns hdw-r
        ip -n hdw-s link add eth0 type veth peer name right netns hdw-r
        ip -n hdw-c address add 10.10.1.2/24 dev eth0
        ip -n hdw-r address add 10.10.1.1/24 dev left
        ip -n hdw-r address add 10.10.2.1/24 dev right
        ip -n hdw-s address add 10.10.2.2/24 dev eth0
        ip -n hdw-c link set eth0 up
        ip -n hdw-r link set left up
        ip -n hdw-r link set right up
        ip -n hdw-s link set eth0 up
        ip -n hdw-c route add default via 10.10.1.1
        ip -n hdw-s route add default via 10.10.2.1
        ip netns exec hdw-r sysctl -qw net.ipv4.ip_forward=0
        trap - EXIT INT TERM
        printf '%s\n' 'Lab created. IPv4 forwarding is OFF for the first experiment.'
        ;;
    down)
        cleanup
        printf '%s\n' 'Lab cleanup complete (or no recorded lab was present).'
        ;;
    *) fail "Usage: sudo bash labs/network.sh up|down" ;;
esac
