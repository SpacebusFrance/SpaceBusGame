from engine.utils.logger import Logger


class ParamUtils:
    """
    A simple wrapper for reading .ini file
    """
    @staticmethod
    def smart_cast(s):
        if isinstance(s, str):
            try:
                # todo: remove eval and do naive cast
                return eval(s.strip())
            except (NameError, SyntaxError):
                return s.strip()
        else:
            return s

    @staticmethod
    def strip_list(l):
        return list(map(str.strip, l))

    @staticmethod
    def string_to_list(s):
        if isinstance(s, str) and ',' in s:
            return ParamUtils.strip_list(s.split(','))
        return s

    @staticmethod
    def parse_string(s, cast=True):
        """
        A simple parser for strings
        :param s:
        :param cast:
        :return:
        """
        if '[' in s or '(' in s or '{' in s or ',' in s:
            if s.startswith('{'):
                # it is a dict
                s = s.replace('{', '').replace('}', '').strip()
                l = dict()
                parts = s.split(",")
                for e in parts:
                    if len(e) > 0:
                        if cast:
                            l[ParamUtils.smart_cast(e.split(':')[0].strip())] = ParamUtils.smart_cast(e.split(':')[1].strip())
                        else:
                            l[e.split(':')[0].strip()] = e.split(':')[1].strip()
                return l
            else:
                # it is a list or tuple
                l = list()
                is_tuple = '(' in s
                parts = s.replace('[', '').replace(']', '').replace('(', '').replace(')', '').split(",")
                for e in parts:
                    if len(e) > 0:
                        if cast:
                            l.append(ParamUtils.smart_cast(e.strip()))
                        else:
                            l.append(e.strip())
                return l if not is_tuple else tuple(l)
        elif cast:
            return ParamUtils.smart_cast(s.strip())
        else:
            return s.strip()

    @staticmethod
    def read_ini_file(file_name, cast=True, use_categories=False):
        file = open(file_name, "r")
        lines = file.readlines()
        file.close()
        categories = dict()
        current_category = None
        params = dict()
        previous = [None, None]
        for line in lines:
            if not line.strip().startswith(';'):
                if '=' in line:
                    # add the previous value
                    if previous[0] is not None:
                        params[previous[0]] = ParamUtils.parse_string(previous[1], cast=cast)
                    previous[0] = line.split("=")[0].strip()
                    previous[1] = line.split("=")[1].strip()
                elif line.strip().startswith('[') and use_categories:
                    if current_category is not None:
                        categories[current_category] = params.copy()
                        params.clear()
                    # new category
                    current_category = line.strip().split(']')[0].replace('[', '').strip()
                elif not line.strip().startswith('['):
                    # it is not a comment but if belongs to the previous line
                    previous[1] += line.strip()

        # adding the last value
        if previous[0] is not None:
            params[previous[0]] = ParamUtils.parse_string(previous[1], cast=cast)
        if use_categories:
            categories[current_category] = params
            return categories
        else:
            return params


def read_file_as_list(file_name, cast=True):
    file = open(file_name, "r")
    lines = file.readlines()
    file.close()
    l = []
    if cast:
        for line in lines:
            l.append(ParamUtils.smart_cast(line.strip()))
    else:
        for line in lines:
            l.append(line.strip())
    return l
