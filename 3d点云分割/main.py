import asyncio
import yaml
from pathlib import Path

from browser.controller import BrowserController
from data.fetcher import DataFetcher
from data.annotation_encoder import build_annotation_result, update_task_data
from data.submitter import Submitter
from segmentation.ground_ransac import extract_ground_ransac
from segmentation.height_filter import classify_by_height
from segmentation.noise_filter import detect_noise
from utils.logger import setup_logger
from utils.screenshot import save_screenshot


async def heartbeat_loop(ctrl: BrowserController, interval: int):
    while True:
        await asyncio.sleep(interval)
        await ctrl.heartbeat()


async def main():
    config_path = Path(__file__).parent / "config.yaml"
    config = yaml.safe_load(config_path.read_text())
    logger = setup_logger(config["logging"]["log_file"])
    logger.info("Starting point cloud automation")

    ctrl = BrowserController(
        config["browser"]["cdp_url"],
        config["browser"]["annotation_title_contains"],
        config["browser"]["annotation_url_host"],
    )
    page = await ctrl.connect()
    logger.info("Connected to browser, page=%s", page.url)

    fetcher = DataFetcher(config)
    submitter = Submitter(config)

    heartbeat_task = asyncio.create_task(
        heartbeat_loop(ctrl, config["heartbeat"]["interval_seconds"])
    )

    try:
        task_data = await fetcher.fetch_task_data(page)
        if task_data is None:
            logger.error("Failed to fetch taskData")
            raise RuntimeError("TaskData fetch failed")

        annotation_template = await fetcher.fetch_annotation_template(page)
        if annotation_template is None:
            logger.error("Failed to fetch annotation template")
            raise RuntimeError("Annotation template fetch failed")

        labels_by_frame = []
        for frame_idx in [0, 1]:
            logger.info("Processing frame %s", frame_idx)
            await save_screenshot(page, f"frame_{frame_idx}_start", config["logging"]["screenshot_dir"])

            points = None
            for attempt in range(3):
                try:
                    points = await fetcher.fetch(page, frame_index=frame_idx)
                    if points is not None:
                        break
                except Exception as e:
                    logger.warning("Fetch attempt %d failed: %s", attempt + 1, e)
                await asyncio.sleep(1)

            if points is None:
                logger.error("Failed to fetch point cloud for frame %s", frame_idx)
                raise RuntimeError("Data fetch failed")
            logger.info("Fetched %d points for frame %s", len(points), frame_idx)

            ground_mask = extract_ground_ransac(
                points,
                max_trials=config["segmentation"]["ransac_max_trials"],
                residual_threshold=config["segmentation"]["ransac_residual_threshold"],
                min_samples=config["segmentation"]["ransac_min_samples"],
            )
            classified = classify_by_height(points, ground_mask, config["segmentation"]["ground_height_tolerance"])
            noise_mask = detect_noise(
                points,
                n_neighbors=config["segmentation"]["noise_neighbors"],
                radius=config["segmentation"]["noise_radius"],
            )

            labels = {
                "ground": classified["ground"],
                "non_ground": classified["non_ground"] & ~noise_mask,
                "noise": noise_mask,
            }
            logger.info(
                "Labels: ground=%d non_ground=%d noise=%d",
                int(labels["ground"].sum()),
                int(labels["non_ground"].sum()),
                int(labels["noise"].sum()),
            )
            labels_by_frame.append(labels)

        category_map = {
            "ground": "0",
            "non_ground": "1",
            "noise": "255",
        }
        annotation_result = build_annotation_result(annotation_template, labels_by_frame, category_map)
        updated_task_data_b64 = update_task_data(task_data, annotation_result)

        result = await submitter.submit_via_api(page, updated_task_data_b64)
        if result is None:
            logger.error("API submit failed, falling back to UI")
            await submitter.submit_via_ui(page)

        await save_screenshot(page, "submitted", config["logging"]["screenshot_dir"])
        logger.info("Submitted trial")
    except Exception as e:
        logger.exception("Automation failed: %s", e)
        await save_screenshot(page, "error", config["logging"]["screenshot_dir"])
        raise
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        await ctrl.close()


if __name__ == "__main__":
    asyncio.run(main())
