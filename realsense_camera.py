"""Read D435i accelerometer and print pitch (deg) for camera mount adjustment. Best when ~still."""
import math

import pyrealsense2 as rs


def accel_to_pitch_deg(ax: float, ay: float, az: float) -> float:
    return math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))


def main():
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.accel, rs.format.motion_xyz32f, 250)

    pipeline.start(config)

    print("Pitch from accel (deg). Ctrl+C to stop.\n")

    try:
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
                pitch = accel_to_pitch_deg(ax, ay, az)
                print(f"pitch={pitch:7.2f}°", end="\r", flush=True)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        pipeline.stop()


if __name__ == "__main__":
    main()
