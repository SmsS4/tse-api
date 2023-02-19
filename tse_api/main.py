import time
from concurrent.futures import ThreadPoolExecutor

from glogger.logger import get_logger
from tse_api.api import TseApi

logger = get_logger("test")


def worker(tse, code):
    if tse.get_live_data(code) is None:
        logger.error("failed")


def main():
    tse = TseApi()
    code = 55924039170758349
    logger.info(
        tse.get_static_data(code)
    )  # to avoid getting static data for each worker
    # pprint(tse.get_live_data(code))

    current = time.time()
    number_of_works = 200
    number_of_workers = 30
    thread_pool = ThreadPoolExecutor(max_workers=number_of_workers)
    for i in range(number_of_works):
        thread_pool.submit(worker, tse, code)
    thread_pool.shutdown(wait=True)
    logger.info("time: %s", (time.time() - current))


if __name__ == "__main__":
    main()
