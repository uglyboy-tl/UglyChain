import pytest

from examples.schema import ClassifyResponse
from uglychain import Model
from uglychain.worker.classify import Classify


@pytest.mark.parametrize(
    "model",
    [
        Model.GPT3_TURBO,
        Model.YI,
        Model.YI_LONGCONTEXT,
        Model.YI_FUNCTION,
        Model.QWEN,
        Model.GLM3,
        Model.BAICHUAN_TURBO,
        Model.OLLAMA,
    ],
)
def test_classify(model):
    worker = Classify(model=model, label=ClassifyResponse)

    input = [
        "加拿大（英语/法语：Canada），首都渥太华，位于北美洲北部。东临大西洋，西濒太平洋，西北部邻美国阿拉斯加州，南接美国本土，北靠北冰洋。气候大部分为亚寒带针叶林气候和湿润大陆性气候，北部极地区域为极地长寒气候。",
        "《琅琊榜》是由山东影视传媒集团、山东影视制作有限公司、北京儒意欣欣影业投资有限公司、北京和颂天地影视文化有限公司、北京圣基影业有限公司、东阳正午阳光影视有限公司联合出品，由孔笙、李雪执导，胡歌、刘涛、王凯、黄维德、陈龙、吴磊、高鑫等主演的古装剧。",
        "《满江红》是由张艺谋执导，沈腾、易烊千玺、张译、雷佳音、岳云鹏、王佳怡领衔主演，潘斌龙、余皑磊主演，郭京飞、欧豪友情出演，魏翔、张弛、黄炎特别出演，许静雅、蒋鹏宇、林博洋、飞凡、任思诺、陈永胜出演的悬疑喜剧电影。",
        "布宜诺斯艾利斯（Buenos Aires，华人常简称为布宜诺斯）是阿根廷共和国（the Republic of Argentina，República Argentina）的首都和最大城市，位于拉普拉塔河南岸、南美洲东南部、河对岸为乌拉圭东岸共和国。",
        "张译（原名张毅），1978年2月17日出生于黑龙江省哈尔滨市，中国内地男演员。1997年至2006年服役于北京军区政治部战友话剧团。2006年，主演军事励志题材电视剧《士兵突击》。",
    ]

    result = worker.run(input)
    assert len(result) == 5
    assert result[0].label.name == "COUNTRY"
    assert result[1].label.name == "TV"
    assert result[2].label.name == "MOVIE"
    assert result[3].label.name == "CITY"
    assert result[4].label.name == "PERSON"
