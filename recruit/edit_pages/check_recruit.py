from client.edit.log_color import (log_info, log_error)
from client.edit.utility import (try_except, time_it)
from recruit.models import (Recruiter)


@try_except
@time_it
def recruit_check(some_one):  # TeamRome
    """ список карточек c id клиента.
    Список Юзеров с зарегистрированной карточкой Сотрудника КЦ. """
    recruit_id_list = [i.recruiter_id for i in Recruiter.objects.all()]
    log_info("\trecruit_id_list: %s" % recruit_id_list)

    """ Имя юзера и его ID. """
    log_info("\tuser_name: %s, user_id: %s" % (some_one, some_one.id))

    """ Проверка: есть ли текущий Юзер в списке Сотрудников КЦ. """
    if some_one.id in recruit_id_list:
        """ Если он есть - возвращаем Объект Сотрудника/рекрутера. """
        recruit = Recruiter.objects.get(recruiter=some_one)
        log_info("\trecruit_id: %s" % recruit.id)
        return recruit
    else:
        log_error('\tRecruit profile DO NOT exists!')
        return None
