import dataclasses
import datetime
import enum
import queue
import time
from queue import Empty
from typing import List
from typing import Optional

# TODO: remove __slots__ and use slots=True in `dataclasses.dataclass`
@dataclasses.dataclass
class BestLimit:
    """
    Order book
    """

    __slots__ = (
        "price",
        "vol",
        "count",
    )
    price: int
    vol: int
    count: int

    def __eq__(self, other: "BestLimit"):
        return (
            self.price == other.price
            and self.vol == other.vol
            and self.count == other.count
        )


@dataclasses.dataclass
class RealLegal:
    """
    Real legal data

    Attributes:
        real_vol: حجم حقیقی
        real_count: تعداد حقیقی
        legal_vol: حجم حقوقی
        legal_count: تعداد حقوقی
    """

    __slots__ = (
        "real_vol",
        "real_count",
        "legal_vol",
        "legal_count",
    )
    real_vol: int
    real_count: int
    legal_vol: int
    legal_count: int

    def __eq__(self, other):
        return (
            self.real_vol == other.real_vol
            and self.real_count == other.real_count
            and self.legal_vol == other.legal_vol
            and self.legal_count == other.legal_count
        )

    def __str__(self):
        return "\t".join(
            [
                f"real_vol: {self.real_vol}",
                f"real_count: {self.real_count}",
                f"legal_vol: {self.legal_vol}",
                f"legal_count: {self.legal_count}",
            ]
        )


class MarketType(enum.Enum):
    """
    Market type

    EXCHANGE: bourse
    FARA_BOURSE: fara bourse
    FIXED_INCOME: sandogh ba dar amad sabet
    """

    EXCHANGE = "ExchangeStock"
    FARA_BOURSE = "FaraBourseStock"
    FARA_BOURSE_BASE = "FaraBourseBase"
    FIXED_INCOME = "FIXED_INCOME"
    SANDOUGH_SAHAMI = "SandoghSahami"

    def __str__(self):
        return str(self.value)


class State(enum.Enum):
    """
    State of instrument
    """

    Allow = "A"  # مجاز
    Allow_Blocked = "AG"  # مجاز مسدود
    Allow_Stopped = "AS"  # مجاز متوقف
    Allow_Hold = "AR"  # مجاز محفوظ
    Forbiden = "I"  # ممنوع
    Forbiden_Blocked = "IG"  # ممنوع مسدود
    Forbiden_Stopped = "IS"  # ممنوع متوقف
    Forbiden_Hold = "IR"  # ممنوع محفوظ
    UNKNOWN = ""  # نامشخص

    def persian(self) -> str:
        if self == State.Allow:
            return "مجاز"
        if self == State.Allow_Blocked:
            return "مجاز مسدود"
        if self == State.Allow_Stopped:
            return "مجاز متوقف"
        if self == State.Allow_Hold:
            return "مجاز محفوظ"
        if self == State.Forbiden:
            return "ممنوع"
        if self == State.Forbiden_Blocked:
            return "ممنوع مسدود"
        if self == State.Forbiden_Stopped:
            return "ممنوع متوقف"
        if self == State.Forbiden_Hold:
            return "ممنوع محفوظ"
        if self == State.UNKNOWN:
            return "نامشخص"
        raise Exception()

    def __str__(self):
        return str(self.value)


@dataclasses.dataclass
class StaticInstrumentInfo:
    """
    Basic instrument info that doesn't change in day

    Attributes:
        name: نام نماد
        full_name: نام بلند شرکت
        instrument_id: کد ۱۲ رقمی نماد
        ins_code: کد ۱۷ رقمی بورس
        min_week: کمینه بازه هفته
        max_week: بیشینه بازه هفته
        min_year: کیمنه بازه سال
        max_year: بیشینه بازه سال
        base_vol: حجم مبنا
        low_threshold: کمینه قیمت مجاز
        high_threshold: بیشیشنه قیمت مجاز
        nav: ناو
        sector_pe: سکتور پی ای
        number_of_shares: تعداد سهام
        month_average_vol: میانگین حجم ماهانه
        industry_sector_code: کد گروه صنعت
        instrument_group_code: کد گروه نماد
        date: date of data (YYYY/MM/DD format) (use datetime_to_date)

    """

    __slots__ = (
        "name",
        "full_name",
        "instrument_id",
        "ins_code",
        "type",
        "min_week",
        "max_week",
        "min_year",
        "max_year",
        "base_vol",
        "low_threshold",
        "high_threshold",
        "nav",
        "sector_pe",
        "number_of_shares",
        "month_average_vol",
        "industry_sector_code",
        "industry_sector_name",
        "industry_subsector_code",
        "industry_subsector_name",
        "instrument_group_code",
        "yesterday_final",
        "index_coefficient",
        "flow",
        "date",
    )
    name: str
    full_name: str
    instrument_id: str
    ins_code: str
    type: MarketType | None
    min_week: int
    max_week: int
    min_year: int
    max_year: int
    base_vol: int
    low_threshold: int
    high_threshold: int
    nav: float
    sector_pe: Optional[float]
    number_of_shares: int
    month_average_vol: int
    industry_sector_code: int
    industry_sector_name: str
    industry_subsector_code: int
    industry_subsector_name: str
    instrument_group_code: int
    yesterday_final: int
    index_coefficient: int
    flow: int  # bource, farabource and ...
    date: str

    def clone(self) -> "StaticInstrumentInfo":
        """
        Clone
        """
        return StaticInstrumentInfo(
            name=self.name,
            full_name=self.full_name,
            instrument_id=self.instrument_id,
            ins_code=self.ins_code,
            type=self.type,
            min_week=self.min_week,
            max_week=self.max_week,
            min_year=self.min_year,
            max_year=self.max_year,
            base_vol=self.base_vol,
            low_threshold=self.low_threshold,
            high_threshold=self.high_threshold,
            nav=self.nav,
            sector_pe=self.sector_pe,
            number_of_shares=self.number_of_shares,
            month_average_vol=self.month_average_vol,
            industry_sector_code=self.industry_sector_code,
            industry_sector_name=self.industry_sector_name,
            industry_subsector_code=self.industry_subsector_code,
            industry_subsector_name=self.industry_subsector_name,
            instrument_group_code=self.instrument_group_code,
            yesterday_final=self.yesterday_final,
            index_coefficient=self.index_coefficient,
            flow=self.flow,
            date=self.date,
        )

    @staticmethod
    def datetime_to_date(  # pylint:disable=missing-function-docstring
        dt: datetime.datetime,
    ) -> str:
        return dt.strftime("%Y/%m/%d")


@dataclasses.dataclass
class Instrument:
    """
    Instrument data class

    Attributes:
        state: وضعیت
        last: آخرین قیمت
        final: قیمت پایانی
        trades_value: ارزش معاملات
        trades_count: تعداد معاملات
        trades_vol: حجم معاملات
        market_value: ارزش بازار
        lowest_price: کف بازه روز
        highest_price: سقف بازه روز
        buy_best_limit: اردر بوک خرید
        sell_best_limit: اردر بوک فروش
        buy_reallegal: داده دیتای حقیقی حقوقی خرید
        sell_reallegal: داده دیتای حقیقی حقوقی فروش
        last_trade_date: آخرین اطلاعات قیمت
        create_date: زمانی که دیتا رو از منبع گرفتیم

    """

    def clone(self) -> "Instrument":
        """
        Clone object
        """
        return Instrument(
            static_data=self.static_data.clone(),
            state=self.state,
            last=self.last,
            final=self.final,
            trades_value=self.trades_value,
            trades_count=self.trades_count,
            trades_vol=self.trades_vol,
            market_value=self.market_value,
            lowest_price=self.lowest_price,
            highest_price=self.highest_price,
            buy_best_limit=[
                BestLimit(
                    price=bl.price,
                    vol=bl.vol,
                    count=bl.count,
                )
                for bl in self.buy_best_limit
            ],
            sell_best_limit=[
                BestLimit(
                    price=bl.price,
                    vol=bl.vol,
                    count=bl.count,
                )
                for bl in self.sell_best_limit
            ],
            buy_reallegal=RealLegal(
                real_vol=self.buy_reallegal.real_vol,
                real_count=self.buy_reallegal.real_count,
                legal_vol=self.buy_reallegal.legal_vol,
                legal_count=self.buy_reallegal.legal_count,
            ),
            sell_reallegal=RealLegal(
                real_vol=self.sell_reallegal.real_vol,
                real_count=self.sell_reallegal.real_count,
                legal_vol=self.sell_reallegal.legal_vol,
                legal_count=self.sell_reallegal.legal_count,
            ),
            last_trade_date=self.last_trade_date,
            create_date=self.create_date,
        )

    def __eq__(self, other: "Instrument") -> bool:  # pylint:disable=too-many-branches
        if (
            self.state != other.state
            or self.last != other.last
            or self.final != other.final
            or self.trades_value != other.trades_value
            or self.trades_count != other.trades_count
            or self.trades_vol != other.trades_vol
            or self.market_value != other.market_value
            or self.lowest_price != other.lowest_price
            or self.highest_price != other.highest_price
            or self.last_trade_date != other.last_trade_date
        ):
            return False
        if len(self.buy_best_limit) != len(other.buy_best_limit):
            return False
        if len(self.sell_best_limit) != len(other.sell_best_limit):
            return False
        for i in range(len(self.buy_best_limit)):
            if self.buy_best_limit[i] != other.buy_best_limit[i]:
                return False
        for i in range(len(self.sell_best_limit)):
            if self.sell_best_limit[i] != other.sell_best_limit[i]:
                return False
        if self.buy_reallegal != other.buy_reallegal:
            return False
        if self.sell_reallegal != other.sell_reallegal:
            return False
        if self.static_data.date != other.static_data.date:
            return False
        return True

    def get_buy_queue(self) -> BestLimit:
        """
        Gets buy queue
        if instrument in not in buy queue
        returns BestLimit(0, 0, 0)

        """
        if self.static_data.high_threshold == self.buy_best_limit[0].price:
            return BestLimit(
                self.buy_best_limit[0].price,
                self.buy_best_limit[0].vol,
                self.buy_best_limit[0].count,
            )
        return BestLimit(0, 0, 0)

    def get_sell_queue(self) -> BestLimit:
        """
        Gets sell queue
        if instrument in not in sell queue
        returns BestLimit(0, 0, 0)

        """
        if self.static_data.low_threshold == self.sell_best_limit[0].price:
            return BestLimit(
                self.sell_best_limit[0].price,
                self.sell_best_limit[0].vol,
                self.sell_best_limit[0].count,
            )
        return BestLimit(0, 0, 0)

    def get_percent_last(self, rlt: bool = False) -> str:
        """
        Gets percent price of last price
        """
        if not rlt:
            return "{:.2f}".format(
                100 * (self.last / self.static_data.yesterday_final - 1)
            )
        sign = "" if self.last > self.static_data.yesterday_final else "-"
        return "{:.2f}{}".format(
            abs(100 * (self.last / self.static_data.yesterday_final - 1)), sign
        )

    def get_power(  # pylint:disable=too-many-return-statements
        self, buy: bool = True
    ) -> float:
        """
        Gets buy/sell real power of instrument
        """
        if self.sell_reallegal.real_count == 0:
            return 0
        if self.buy_reallegal.real_count == 0:
            return 0
        if self.sell_reallegal.real_vol == 0:
            return 0
        if self.buy_reallegal.real_vol == 0:
            return 0
        result = (self.buy_reallegal.real_vol / self.buy_reallegal.real_count) / (
            self.sell_reallegal.real_vol / self.sell_reallegal.real_count
        )
        if buy:
            return result
        if not result:
            return 0
        return 1 / result

    def get_density(self, buy=True) -> int:
        """
        Gets buy/sell real density of instrument
        """
        if buy:
            reallegal = self.buy_reallegal
        else:
            reallegal = self.sell_reallegal
        if not reallegal.real_count:
            return 0
        return (self.final * reallegal.real_vol) // reallegal.real_count

    __slots__ = (
        "static_data",
        "state",
        "last",
        "final",
        "trades_value",
        "trades_count",
        "trades_vol",
        "market_value",
        "lowest_price",
        "highest_price",
        "buy_best_limit",
        "sell_best_limit",
        "buy_reallegal",
        "sell_reallegal",
        "last_trade_date",
        "create_date",
    )
    static_data: StaticInstrumentInfo
    state: State
    last: int
    final: int
    trades_value: int
    trades_count: int
    trades_vol: int
    market_value: int
    lowest_price: int
    highest_price: int
    buy_best_limit: List[BestLimit]
    sell_best_limit: List[BestLimit]
    buy_reallegal: RealLegal
    sell_reallegal: RealLegal
    last_trade_date: str
    create_date: datetime.datetime


class Observer:
    """
    Observer class
    """

    def __init__(self):
        # self.__queue = Manager().Queue()
        self.__queue = queue.Queue()
        self.__static = {}

    def qsize(self) -> int:
        """
        Size of queue
        """
        return self.__queue.qsize()

    def put(self, data: Instrument) -> None:
        """
        Put data to observer
        """
        self.__queue.put(data)

    def get(self) -> Instrument:
        """
        Gets new data.
        This method blocks till a new data is available
        """
        while True:
            try:
                instrument = self.__queue.get(block=True, timeout=1)
                break
            except Empty:
                print("empty")
                time.sleep(1)
        # queue send data by value
        # so for memory optimization we need
        # to only store static_data once
        key = (instrument.static_data.instrument_id, instrument.static_data.date)
        if key not in self.__static:
            self.__static[key] = instrument.static_data
        if (
            self.__static[key].low_threshold == instrument.static_data.low_threshold
            and self.__static[key].high_threshold
            == instrument.static_data.high_threshold
        ):
            instrument.static_data = self.__static[key]
        else:
            self.__static[key] = instrument.static_data
        return instrument


class CurrencyType(enum.Enum):
    DOLLAR = 1
    RIAL = 2
    NONE = 3


@dataclasses.dataclass
class InstrumentInfo:
    """
    Basic instrument info
    """

    __slots__ = (
        "name",
        "instrument_id",
        "ins_code",
        "type",
        "group_id",
        "group_name",
        "currency",
    )
    name: str
    instrument_id: str
    ins_code: str
    type: MarketType
    group_id: int
    group_name: str
    currency: CurrencyType


@dataclasses.dataclass
class DetailForOrder:
    __slots__ = (
        "state",
        "threshold_low",
        "threshold_high",
        "buy_lot",
        "sell_lot",
        "asset",
    )
    state: State
    threshold_low: int
    threshold_high: int
    buy_lot: int
    sell_lot: int
    asset: int
