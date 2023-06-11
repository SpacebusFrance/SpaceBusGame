import logging

logging.basicConfig(
    format='%(levelname)s [%(asctime)s]: %(message)s',
    level=logging.INFO)

Logger = logging
Logger.title = logging.info
Logger.print = logging.info

# class Logger:
#     colors = {'purple': '\033[95m',
#               'blue': '\033[94m',
#               'green': '\033[92m',
#               'yellow': '\033[93m',
#               'red':  '\033[91m',
#               'end':  '\033[0m',
#               'bold':  '\033[1m',
#               'underline':  '\033[4m'
#               }
#
#     @staticmethod
#     def print(*args, key='', color=None, fmt=None):
#         pre = Logger.colors.get(color, '')
#         if isinstance(fmt, list):
#             for key in fmt:
#                 pre += Logger.colors.get(key, '')
#         else:
#             pre += Logger.colors.get(fmt, '')
#
#         if len(pre) > 0:
#             print(pre, key,  *args, Logger.colors['end'])
#         else:
#             print(key, *args)
#
#     @staticmethod
#     def title(*args):
#         Logger.info(*args)
#
#     @staticmethod
#     def info(*args):
#         Logger.info(*args)
#
#     @staticmethod
#     def warning(*args):
#         Logger.info(*args)
#
#     @staticmethod
#     def error(*args):
#         Logger.info(*args)
