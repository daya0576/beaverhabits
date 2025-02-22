import datetime
from dateutil.relativedelta import relativedelta
from nicegui import ui

from beaverhabits.frontend import icons
from beaverhabits.sql.models import Habit

async def habit_history(habit: Habit, today: datetime.date):
    # Get completed days from checked_records
    completed_days = [record.day for record in habit.checked_records if record.done]
    
    # get latest 6 months, e.g. Feb
    months, data = [], []
    for i in range(13, 0, -1):
        offset_date = today - relativedelta(months=i)
        months.append(offset_date.strftime("%b"))

        count = sum(
            1
            for day in completed_days
            if day.month == offset_date.month and day.year == offset_date.year
        )
        data.append(count)

    echart = ui.echart(
        {
            "xAxis": {
                "data": months,
            },
            "yAxis": {
                "type": "value",
                "position": "right",
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#303030",
                    },
                },
            },
            "series": [
                {
                    "type": "line",
                    "data": data,
                    "itemStyle": {"color": icons.current_color},
                    "animation": False,
                }
            ],
            "grid": {
                "top": 15,
                "bottom": 25,
                "left": 5,
                "right": 30,
                "show": False,
            },
        }
    )
    echart.classes("h-40")
