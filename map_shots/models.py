from django.contrib.postgres.fields import ArrayField
from django.core.files.base import ContentFile
from django.db import models

from map_shots.api import YandexStaticMap
from map_shots.manager import GeoSquareManager


class GeoSquare(models.Model):
    """
    Георграфический "квадрат" :)
    """
    name = models.CharField(
        verbose_name=u'Название квадрата',
        max_length=255,
        blank=False,
    )
    enabled = models.BooleanField(
        verbose_name='Включен',
        default=True,
    )
    start_latlng = ArrayField(
        verbose_name='Начальная точка',
        base_field=models.DecimalField(
            decimal_places=6,
            max_digits=9,
        ),
    )
    end_latlng = ArrayField(
        verbose_name='Конечная точка',
        base_field=models.DecimalField(
            decimal_places=6,
            max_digits=9,
        ),
    )

    enabled_squares = GeoSquareManager()

    class Meta:
        verbose_name = 'Квадрат'
        verbose_name_plural = 'Квадраты'

    def __str__(self):
        return self.name

    def get_latitude_width(self):
        """
        получить ширину широты квадрата
        """
        start_latitude, end_latitude = self.start_latlng[0], self.end_latlng[0]
        return abs(start_latitude - end_latitude)

    def make_shot(self):
        """
        сделать снимок
        :return:
        """
        print(f'square {self}')

        point_list = YandexStaticMap.create_point_list(
            self.start_latlng,
            self.end_latlng,
        )

        shot = Shot.objects.create(square=self)

        for idx, point in enumerate(point_list):
            result_bytes = YandexStaticMap.get_image(lanlng=point)
            shotpart = ShotPart(
                number=idx,
                shot=shot,
                latlng=point,
            )
            shotpart.image.save(
                f'{idx}-{"-".join(map(str, point))}.png',
                ContentFile(result_bytes),
                save=True
            )

        shot.join_shotparts()


class Shot(models.Model):
    """
    Объединённый сникок карты со слоем пробок на конкретную дату и время
    """
    square = models.ForeignKey(
        GeoSquare,
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
    )
    image = models.ImageField(
        verbose_name='Готовое изображение',
        upload_to='images/%Y/%m/%d/',
        null=True,
    )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now=True,
    )

    class Meta:
        verbose_name = 'снимок'
        verbose_name_plural = 'Снимки'
        ordering = ('created',)

    def __str__(self):
        return f'{self.created}'

    def join_shotparts(self):
        """
        собрать части снимка воедино и сохранить
        """
        complex_image = YandexStaticMap.make_complex_image(
            images_paths_list=list(self.shotpart_set.values_list('image')),
            latitude_width=self.square.get_latitude_width()
        )
        self.image.save(
            f'{self.square_id}_{self.created.strftime("%H-%M")}.jpg',
            complex_image,
        )


class ShotPart(models.Model):
    """
    Часть снимка карты со слоем пробок
    """
    shot = models.ForeignKey(
        Shot,
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        verbose_name='изображение',
        upload_to='images/%Y/%m/%d/%H_%M',
    )
    number = models.IntegerField(
        verbose_name='Номер снимка',
    )
    latlng = ArrayField(
        verbose_name='Координаты',
        base_field=models.DecimalField(
            decimal_places=6,
            max_digits=9,
        ),
    )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now=True,
    )

    class Meta:
        verbose_name = 'часть'
        verbose_name_plural = 'части'
        ordering = ('number',)

    def __str__(self):
        return f'{self.number}'
