"""
Pitch from D435i accelerometer. Pipeline matches visual_extreme_parkour.start_pipeline
(depth + motion) so USB / driver negotiation matches the working stack.
"""
import argparse
import math
import time

import pyrealsense2 as rs


def accel_to_pitch_deg(_ax: float, ay: float, az: float) -> float:
    # D435i horizontal → ay ≈ -g, az ≈ 0.  Pitch = 0° when level; positive = lens tilted downward.
    return math.degrees(math.atan2(az, -ay))


def start_pipeline(width: int, height: int, depth_fps: int):
    """
    Same depth request as VisualHandlerNode.start_pipeline, plus IMU accel.
    Tries several accel rates; depth+accel together often resolves where accel-only fails.
    """
    pipeline = rs.pipeline()
    for accel_fps in (250, 200, 100, 63):
        config = rs.config()
        config.enable_stream(
            rs.stream.depth,
            width,
            height,
            rs.format.z16,
            depth_fps,
        )
        config.enable_stream(
            rs.stream.accel,
            rs.format.motion_xyz32f,
            accel_fps,
        )
        try:
            pipeline.start(config)
            return pipeline, accel_fps
        except RuntimeError:
            continue
    raise RuntimeError(
        "Could not start RealSense depth+accel. "
        "Use a D435i (IMU), close other apps using the camera, "
        "and check `rs-enumerate-devices` for supported streams."
    )


def main():
    parser = argparse.ArgumentParser(description="Print pitch (deg) from RealSense IMU.")
    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="Depth width (same default as visual_extreme_parkour.py)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=480,
        help="Depth height (same default as visual_extreme_parkour.py)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Depth FPS (same default as visual_extreme_parkour.py --fps)",
    )
    parser.add_argument(
        "--print-hz",
        type=float,
        default=5.0,
        metavar="HZ",
        help="How often to print pitch (default: 5). Lower = slower updates.",
    )
    args = parser.parse_args()
    if args.print_hz <= 0:
        raise SystemExit("--print-hz must be positive")
    print_interval = 1.0 / args.print_hz

    pipeline, accel_fps = start_pipeline(args.width, args.height, args.fps)

    print(
        f"Pitch from accel (deg) | depth {args.width}x{args.height}@{args.fps} Hz, "
        f"accel @{accel_fps} Hz, print @{args.print_hz:g} Hz. Ctrl+C to stop.\n"
    )

    try:
        next_print = 0.0
        while True:
            frames = pipeline.wait_for_frames()
            ax = ay = az = None

            for f in frames:
                if not f.is_motion_frame():
                    continue
                mf = f.as_motion_frame()
                if mf.get_profile().stream_type() != rs.stream.accel:
                    continue
                d = mf.get_motion_data()
                ax, ay, az = d.x, d.y, d.z

            if ax is not None:
                now = time.monotonic()
                if now >= next_print:
                    pitch = accel_to_pitch_deg(ax, ay, az)
                    print(f"pitch={pitch:7.2f}°", end="\r", flush=True)
                    next_print = now + print_interval
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        pipeline.stop()


if __name__ == "__main__":
    main()
