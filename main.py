from server.server_run import *

import cProfile
import pstats
import io


main()
#
# # Создаем профилировщик
# profiler = cProfile.Profile()
# profiler.enable()
#
# # Код, который нужно профилировать
#
#
# # Останавливаем профилирование
# profiler.disable()
#
# # Сохраняем результаты в файл
# profiler.dump_stats('fibonacci_profile.prof')
#
# # Или анализируем сразу
# s = io.StringIO()
# stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
# stats.print_stats()
# print(s.getvalue())
#
