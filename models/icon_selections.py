 #main.pyの227行目から挿入


class IconSelections(object):

    def select_flag(self, wind_max):
        """
        風速に合わせて旗画像を選択
        :param wind_max:
        :return:
        """

        if wind_max:
            if wind_max < 3:
                flag_file = "flag_s.png"
            elif wind_max < 7:
                flag_file = "flag_m.png"
            elif wind_max > 12:
                flag_file = "flag_l.png"
            else:
                flag_file = "flag_m.png"
        else:
            flag_file = None

        return flag_file

    def select_compass(self, wind_direction):
        """
        風向に合わせてコンパス画像を選択
        :param wind_direction:
        :return:
        """
        if wind_direction:
            if len(wind_direction) < 1:
                wind_direction_file = None
            else:
                # 変換ルール
                table = str.maketrans({
                    '北': 'n',
                    '南': 's',
                    '西': 'w',
                    '東': 'e',
                })
                # まとめて置換
                _wind_direction_en = str(wind_direction).translate(table)

                # 北はNではなく、NNに
                wind_direction_en = _wind_direction_en + _wind_direction_en if len(_wind_direction_en) == 1 else _wind_direction_en

                # ファイル名
                wind_direction_file = "compass_" + wind_direction_en + ".png"
        else:
            wind_direction_file = None

        return wind_direction_file

    def select_wave(self, sea_surface):
        """
        海面情報に合わせて海面画像を選択
        :param sea_surface:
        :return:
        """
        if sea_surface:
            if sea_surface == "フラット":
                wave_file = "wave_s.png"
            elif sea_surface == "チョッピー":
                wave_file = "wave_m.png"
            elif sea_surface == "高波":
                wave_file = "wave_l.png"
            else:
                wave_file = None
        else:
            wave_file = None

        return wave_file
