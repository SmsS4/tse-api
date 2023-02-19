import datetime
import re
import time
from typing import Tuple, List, Optional, Dict

import requests
from glogger.logger import get_logger

from tse_api import models
from tse_api.defensive import defensive


class InstrumentDeleted(Exception):
    pass


class TseApi:
    """
    Tse API
    """
    # TODO: refactor

    __logger = get_logger("TseApi")

    def __init__(
            self,
            request_timeout: float = 4,
            sleep_tse_errors: float = 5,
            sleep_timeout: float = 1,
            sleep_connection_error: float = 0.1,
            sleep_non_200: float = 1,
    ):
        self.__logger.info("TseApi Init")
        self._static_instrument_data: Dict[str | int, models.StaticInstrumentInfo] = {}
        self.request_timeout = request_timeout
        self.sleep_tse_errors = sleep_tse_errors
        self.sleep_timeout = sleep_timeout
        self.sleep_connection_error = sleep_connection_error
        self.sleep_non_200 = sleep_non_200

    def get(self, url: str, **params) -> str:
        """
        request url with params
        """
        while True:
            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.request_timeout
                )
                result = response.text
                if response.status_code != 200:
                    # TODO seprate 4XX 5XX
                    self.__logger.error("response %d", response.status_code)
                    time.sleep(self.sleep_non_200)
                    continue
                if (
                        "Too Many Requests" in result
                        or "The service is unavailable" in result
                        or "Error" in result
                ):
                    self.__logger.warning(url)
                    self.__logger.warning(result)
                    time.sleep(self.sleep_tse_errors)
                    continue
                return result
            except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
                self.__logger.warning("Timeout in get %s with params %s", url, params)
                time.sleep(self.sleep_timeout)
            except requests.exceptions.ConnectionError:
                self.__logger.warning("Connection error")
                time.sleep(self.sleep_connection_error)

    def get_static_data_retry(self, ins_code: str | int, retry_number: int) -> models.StaticInstrumentInfo:
        """
        Trying to get static data
        """
        for i in range(retry_number):
            try:
                return self.get_static_data(ins_code)
            except Exception as e:
                self.__logger.error("failed %s", e)
                if i == retry_number - 1:
                    raise e
                time.sleep(0.1)

    def get_static_data(  # pylint:disable=too-many-locals, too-many-statements
            self,
            ins_code: str | int
    ) -> models.StaticInstrumentInfo:
        """
        Gets static instrument info (see `models.StaticInstrumentInfo`)

        Notes:
            doesn't set yesterday_final_price
        """

        self.__logger.debug("Getting static data for %s 0/2", ins_code)
        while True:
            try:
                response = self.get(
                    "http://tsetmc.com/Loader.aspx", ParTree=151311, i=ins_code
                )
                result = re.split(
                    "[,;]",
                    re.findall(r"<script>var TopInst[\s\S]*;</script>", response)[0],
                )[:-1]
                break
            except IndexError:
                self.__logger.warning(
                    "Problem in getting data. retry\n%s\n%s", ins_code, response
                )
                time.sleep(1)
                continue
        self.__logger.debug("Getting static data for %s 1/2", ins_code)
        result[0] = result[0].replace("<script>var ", "")
        result = {data.split("=")[0].strip(): data.split("=")[1] for data in result}
        for key in result:
            if result[key][0] == "'":
                result[key] = result[key][1:-1]

        base_vol = int(result["BaseVol"])
        instrument_id = result["InstrumentID"]
        industry_sector_code = int(result["CSecVal"])  # c used for get
        # date = result['DEven']
        # if result['EstimatedEPS']:
        #     eps = int(result['EstimatedEPS'])
        # else:
        #     eps = 0
        flow = int(result["Flow"])  # bource, farabource, ...
        # cisin = result['CIsin']  # کد 12 رقمی شرکت
        full_name = result["LSecVal"]
        name = result["LVal18AFC"]
        max_week = int(float(result["MaxWeek"]))
        min_week = int(float(result["MinWeek"]))
        max_year = int(float(result["MaxYear"]))
        min_year = int(float(result["MinYear"]))
        threshold_high = int(float(result["PSGelStaMax"]))
        threshold_low = int(float(result["PSGelStaMin"]))
        if "NAV" in result:
            nav = float(result["NAV"])
        else:
            nav = None

        if len(result["SectorPE"]):
            sector_pe = float(result["SectorPE"])
        else:
            sector_pe = 0
        shares = int(result["ZTitad"])  # tedad saham
        instrument_group_code = result["CgrValCot"]
        if result["KAjCapValCpsIdx"]:
            index_coefficient = int(result["KAjCapValCpsIdx"])
        else:
            index_coefficient = 0

        month_average_vol = int(result["QTotTran5JAvg"])  # miangin hajm mahane
        response = self.get(
            "http://tsetmc.com/Loader.aspx", Partree="15131M", i=ins_code
        )
        self.__logger.debug("Getting static data for %s 2/2", ins_code)
        result = list(map(str.strip, re.findall(r"<td>(.*?)</td>", response)))
        try:
            assert result[22] == "گروه صنعت"
        except IndexError as e:
            self.__logger.error(ins_code)
            self.__logger.error(response)
            self.__logger.error(result)
            raise e

        industry_sector_name = result[23]
        assert result[24] == "کد زیر گروه صنعت"
        industry_subsector_code = int(result[25])
        assert result[26] == "زیر گروه صنعت"
        industry_subsector_name = result[27]

        result = models.StaticInstrumentInfo(
            name=name,
            full_name=full_name,
            instrument_id=instrument_id,
            ins_code=ins_code,
            type=None,
            min_week=min_week,
            max_week=max_week,
            min_year=min_year,
            max_year=max_year,
            base_vol=base_vol,
            low_threshold=threshold_low,
            high_threshold=threshold_high,
            nav=nav,
            sector_pe=sector_pe,
            number_of_shares=shares,
            month_average_vol=month_average_vol,
            industry_sector_code=industry_sector_code,
            industry_sector_name=industry_sector_name,
            industry_subsector_code=industry_subsector_code,
            industry_subsector_name=industry_subsector_name,
            instrument_group_code=instrument_group_code,
            yesterday_final=-1,
            index_coefficient=index_coefficient,
            flow=flow,
            date=datetime.datetime.now().strftime("%Y/%M/%d"),
        )
        self._static_instrument_data[result.ins_code] = result
        return result

    def __get_best_limits(
            self, all_data: list
    ) -> Tuple[List[models.BestLimit], List[models.BestLimit]]:  # pylint:disable=too-many-locals
        """
        Gets best limits from data
        """
        buy_best_limits = []
        sell_best_limits = []
        best_limits = all_data[2][:-1].split(",")

        if best_limits == [""]:
            best_limits = []

        for bl_data in best_limits:
            bl = list(map(int, bl_data.split("@")))
            buy_count = bl[0]
            buy_vol = bl[1]
            buy_price = bl[2]
            sell_price = bl[3]
            sell_vol = bl[4]
            sell_count = bl[5]
            buy_best_limits.append(
                models.BestLimit(
                    price=buy_price,
                    vol=buy_vol,
                    count=buy_count,
                )
            )
            sell_best_limits.append(
                models.BestLimit(price=sell_price, vol=sell_vol, count=sell_count)
            )
        for _ in range(5 - len(best_limits)):
            buy_best_limits.append(
                models.BestLimit(
                    price=0,
                    vol=0,
                    count=0,
                )
            )
            sell_best_limits.append(models.BestLimit(price=0, vol=0, count=0))
        return buy_best_limits, sell_best_limits

    def __get_reallegal(
            self, all_data: list
    ) -> Tuple[Optional[models.RealLegal], Optional[models.RealLegal]]:
        """
        Gets reallegal from data
        """
        if all_data[4]:
            data = list(map(int, all_data[4].split(",")))

            real_buy_vol = data[0]
            legal_buy_vol = data[1]
            real_sell_vol = data[3]
            legal_sell_vol = data[4]

            real_buy_count = data[5]
            legal_buy_count = data[6]
            real_sell_count = data[8]
            legal_sell_count = data[9]
            buy_reallegal = models.RealLegal(
                real_vol=real_buy_vol,
                real_count=real_buy_count,
                legal_vol=legal_buy_vol,
                legal_count=legal_buy_count,
            )
            sell_reallegal = models.RealLegal(
                real_vol=real_sell_vol,
                real_count=real_sell_count,
                legal_vol=legal_sell_vol,
                legal_count=legal_sell_count,
            )
            return buy_reallegal, sell_reallegal
        return None, None

    def __check_data(self, data: list, response: str, ins_code: str):
        """
        Checks if response is valid
        """
        try:
            last_trade_date = data[0]
        except IndexError as e:
            self.__logger.error("data[0]")
            self.__logger.error(response)
            self.__logger.error("%s", len(data))
            self.__logger.error("%s", data)
            self.__logger.error("%s", ins_code)
            raise e
        try:
            state = models.State(data[1].strip())
        except IndexError as e:
            self.__logger.error("%s", e)
            self.__logger.error("data[1]")
            self.__logger.error(response)
            self.__logger.error("%s", len(data))
            self.__logger.error("%s", data)
            self.__logger.error("%s", ins_code)
            raise InstrumentDeleted()
        return last_trade_date, state

    @defensive()
    def get_live_data(  # pylint:disable=too-many-locals
            self, ins_code: str | int
    ) -> models.Instrument | None:
        """
        Gets data that changes during day

        Args:
            ins_code: 17 digit instrument id

        Returns:
            None if instrument deleted else Instrument object
        """
        if ins_code not in self._static_instrument_data:
            self.__logger.warning("Getting static data")
            self.get_static_data(ins_code)
        static_data = self._static_instrument_data[ins_code]

        response = self.get(
            "http://tsetmc.com/tsev2/data/instinfodata.aspx",
            i=ins_code,
            c=static_data.industry_sector_code,
        )
        all_data = response.split(";")
        data = all_data[0].split(",")

        # alL_data[0] is price data (last, final, market trades and ...)
        # all_data[1] is index
        # all_data[1] oon chizaye marboot be shakhes o inas ke balaye tse neshoon mide
        # all_data[2] is for best limit
        # all_data[3] is something about messages
        # all_data[4] is real legal data
        # all_data[5] is data of relative companies
        # all_data[6] is always empty
        # if all_data[7][0] == 0 connection is stable
        try:
            last_trade_date, state = self.__check_data(data, response, ins_code)
        except InstrumentDeleted:
            self.__logger.error("%s deleted", ins_code)
            return None
        last = int(data[2])
        final = int(data[3])
        # first = int(data[4])
        yesterday_final = int(data[5])
        today_range_high = int(data[6])
        today_range_low = int(data[7])
        trades_count = int(data[8])
        trades_vol = int(data[9])
        trades_value = int(data[10])
        # market_value = final * ZTitad
        # date = data[12]
        # data[13] is also last trade date!
        buy_best_limits, sell_best_limits = self.__get_best_limits(all_data)
        buy_reallegal, sell_reallegal = self.__get_reallegal(all_data)
        if static_data.flow != 3:
            market_value = final * static_data.number_of_shares
        else:
            if len(all_data[7].split("@")) > 1:
                market_value = all_data[7].split("@")[1]
            else:
                market_value = 0
        static_data.yesterday_final = yesterday_final
        return models.Instrument(
            static_data=static_data,
            state=state,
            last=last,
            final=final,
            trades_value=trades_value,
            trades_count=trades_count,
            trades_vol=trades_vol,
            market_value=market_value,
            lowest_price=today_range_low,
            highest_price=today_range_high,
            buy_best_limit=buy_best_limits,
            sell_best_limit=sell_best_limits,
            buy_reallegal=buy_reallegal,
            sell_reallegal=sell_reallegal,
            last_trade_date=last_trade_date,
            create_date=datetime.datetime.now(),
        )


