"""Preset suggestions for 6 wind turbine component systems."""

PRESET_SUGGESTIONS = {
    "齿轮箱系统": {
        "measures": "1.检查齿轮油品质及油位 2.核实轴承温度测点 3.检查冷却系统运行状态 4.必要时降功率运行",
        "personnel": "齿轮箱检修工2人、状态监测工程师1人",
        "tools": "振动分析仪、油液检测仪、红外测温仪",
        "materials": "齿轮油、密封件、备用轴承",
    },
    "发电机系统": {
        "measures": "1.检查冷却系统流量 2.核实温度测点 3.检查绝缘电阻 4.监测轴承振动",
        "personnel": "发电机检修工2人、电气工程师1人",
        "tools": "兆欧表、红外热像仪、振动检测仪",
        "materials": "绝缘材料、密封件、润滑油",
    },
    "叶片系统": {
        "measures": "1.目视检查叶片表面 2.使用无人机巡检裂纹 3.检查防雷装置 4.必要时停机修复",
        "personnel": "叶片检修工2人、无人机操作员1人",
        "tools": "无人机、探伤仪、游标卡尺",
        "materials": "叶片修补材料、防雷器件、密封胶",
    },
    "变桨系统": {
        "measures": "1.检查变桨轴承磨损 2.核实变桨电机温度 3.检查变桨角度传感器 4.校准变桨限位",
        "personnel": "变桨系统检修工2人",
        "tools": "角度测量仪、振动检测仪、万用表",
        "materials": "备用变桨电机、轴承、传感器",
    },
    "偏航系统": {
        "measures": "1.检查偏航轴承磨损 2.核实偏航电机电流 3.检查偏航计数器 4.润滑偏航齿圈",
        "personnel": "偏航系统检修工2人",
        "tools": "电流钳形表、振动检测仪、润滑脂加注枪",
        "materials": "润滑脂、密封件、备用偏航电机",
    },
    "液压系统": {
        "measures": "1.检查液压油温及油位 2.核实系统压力 3.检查管路接头泄漏 4.更换液压油滤芯",
        "personnel": "液压系统检修工2人",
        "tools": "压力表、红外测温仪、泄漏检测仪",
        "materials": "液压油、滤芯、密封件、管接头",
    },
}


def get_suggestions(system: str) -> dict:
    """Return preset suggestions for the given system name."""
    return PRESET_SUGGESTIONS.get(
        system,
        {
            "measures": "请联系相关技术人员进行检查",
            "personnel": "检修工2人",
            "tools": "常规检修工具",
            "materials": "常规备件",
        },
    )
