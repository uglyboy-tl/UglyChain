# 分类节点
分类节点的作用是利用大模型的能力对信息进行分类，而分类的定义可以完全由用户语言描述的方式来进行。

## 分类信息的数据结构定义
```python
class Label(Enum):
    COUNTRY = "国家"
    CITY = "城市"
    MOVIE = "电影"
    TV = "电视剧"
    PERSON = "人物"


class ClassifyResponse(BaseModel):
    reason: str = Field(..., description="The reason to explain the classification.")
    label: Label = Field(..., description="The label of the classification.")
```

!!! Note
    我们需要的是 `ClassifyResponse` 这个基于 `BaseModel` 的类，以便于生成返回数据的结构。但 `ClassifyResponse` 中，只有 `label` 是必顶的。
    `reason` 是我们建议的一种方式，因为大模型对分类的原因做解释的话，会帮助它得到更好的分类结果。当然这样也会带来一些额外的计算成本，所以可以根据实际情况来决定是否需要。

## 分类节点的使用
```python
worker = Classify(label=ClassifyResponse)
worker.run(
        "《琅琊榜》是由山东影视传媒集团、山东影视制作有限公司、北京儒意欣欣影业投资有限公司、北京和颂天地影视文化有限公司、北京圣基影业有限公司、东阳正午阳光影视有限公司联合出品，由孔笙、李雪执导，胡歌、刘涛、王凯、黄维德、陈龙、吴磊、高鑫等主演的古装剧。"
    )
# 或者并行批量处理
worker.run([
    "加拿大（英语/法语：Canada），首都渥太华，位于北美洲北部。东临大西洋，西濒太平洋，西北部邻美国阿拉斯加州，南接美国本土，北靠北冰洋。气候大部分为亚寒带针叶林气候和湿润大陆性气候，北部极地区域为极地长寒气候。",
    "《琅琊榜》是由山东影视传媒集团、山东影视制作有限公司、北京儒意欣欣影业投资有限公司、北京和颂天地影视文化有限公司、北京圣基影业有限公司、东阳正午阳光影视有限公司联合出品，由孔笙、李雪执导，胡歌、刘涛、王凯、黄维德、陈龙、吴磊、高鑫等主演的古装剧。",
    "《满江红》是由张艺谋执导，沈腾、易烊千玺、张译、雷佳音、岳云鹏、王佳怡领衔主演，潘斌龙、余皑磊主演，郭京飞、欧豪友情出演，魏翔、张弛、黄炎特别出演，许静雅、蒋鹏宇、林博洋、飞凡、任思诺、陈永胜出演的悬疑喜剧电影。",
    "布宜诺斯艾利斯（Buenos Aires，华人常简称为布宜诺斯）是阿根廷共和国（the Republic of Argentina，República Argentina）的首都和最大城市，位于拉普拉塔河南岸、南美洲东南部、河对岸为乌拉圭东岸共和国。",
    "张译（原名张毅），1978年2月17日出生于黑龙江省哈尔滨市，中国内地男演员。1997年至2006年服役于北京军区政治部战友话剧团。2006年，主演军事励志题材电视剧《士兵突击》。",
])
```

## 自定义的分类描述
描述信息是用来帮助大模型更好的理解分类的原因，从而得到更好的分类结果。
这个信息可以放在 `role` 中：
```python
role = "你对分类的描述信息"
worker = Classify(role=role, label=ClassifyResponse)
```

## 提供分类样例
为了让大模型更好的理解分类的原因，我们可以提供一些样例信息，这样大模型就可以更好的理解分类的原因。
```python
samples = ["标签1":"样例1", "标签2":"样例2", "标签3":"样例3"]
worker = Classify(samples=samples, label=ClassifyResponse)
```