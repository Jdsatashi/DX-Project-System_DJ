from django.apps import apps

from utils.env import PGS_DB, PGS_PASSWORD, PGS_USER, PGS_HOST, PGS_PORT
import psycopg2
from psycopg2.extras import RealDictCursor


def get_all_user_perms(user):
    Perm, User, UserGroupPerm, GroupPerm, UserPerm, GroupPermPerms = get_user_model()

    direct_perms = Perm.objects.filter(userperm__user=user)

    group_perms = Perm.objects.filter(
        grouppermperms__group__usergroupperm__user=user,
        grouppermperms__group__usergroupperm__allow=True
    )

    all_perms = direct_perms | group_perms
    all_perms = all_perms.distinct()

    return all_perms


def get_all_user_perms_sql(user_id):
    Perm, User, UserGroupPerm, GroupPerm, UserPerm, GroupPermPerms = get_user_model()

    conn = psycopg2.connect(
        dbname=PGS_DB,
        user=PGS_USER,
        password=PGS_PASSWORD,
        host=PGS_HOST,
        port=PGS_PORT
    )
    cur = conn.cursor()

    perm_table = Perm._meta.db_table
    user_perm_table = UserPerm._meta.db_table
    group_perm_table = GroupPerm._meta.db_table
    user_group_perm_table = UserGroupPerm._meta.db_table
    groupperm_perm_table = GroupPermPerms._meta.db_table

    # Truy vấn lấy các quyền trực tiếp của người dùng
    direct_perms_query = f"""
        SELECT p.*
        FROM {perm_table} p
        JOIN {user_perm_table} up ON p.name = up.perm_id
        WHERE up.user_id = %s
    """

    # Truy vấn lấy các quyền từ các GroupPerm mà người dùng thuộc về
    group_perms_query = f"""
        SELECT p.*
        FROM {perm_table} p
        JOIN {groupperm_perm_table} gpp ON p.name = gpp.perm_id
        JOIN {group_perm_table} gp ON gpp.group_id = gp.name
        JOIN {user_group_perm_table} ugp ON gp.name = ugp.group_id
        WHERE ugp.user_id = %s AND ugp.allow = TRUE
    """

    cur.execute(direct_perms_query, (user_id,))
    direct_perms = cur.fetchall()

    cur.execute(group_perms_query, (user_id,))
    group_perms = cur.fetchall()

    cur.close()
    conn.close()

    perm_names = [perm[0] for perm in direct_perms + group_perms]
    perm_objs = Perm.objects.filter(name__in=perm_names).distinct()
    return list(perm_objs)


def get_user_by_permname_sql(perm_name):
    Perm, User, UserGroupPerm, GroupPerm, UserPerm, GroupPermPerms = get_user_model()

    conn = psycopg2.connect(
        dbname=PGS_DB,
        user=PGS_USER,
        password=PGS_PASSWORD,
        host=PGS_HOST,
        port=PGS_PORT
    )
    cur = conn.cursor()

    user_table = User._meta.db_table
    user_group_perm_table = UserGroupPerm._meta.db_table
    group_perm_table = GroupPerm._meta.db_table
    user_perm_table = UserPerm._meta.db_table
    perm_table = Perm._meta.db_table
    groupperm_perm_table = GroupPermPerms._meta.db_table

    query = f"""
        SELECT DISTINCT u.id
        FROM {user_table} u
        LEFT JOIN {user_group_perm_table} ugp ON u.id = ugp.user_id
        LEFT JOIN {group_perm_table} gp ON ugp.group_id = gp.name
        LEFT JOIN {groupperm_perm_table} gpp ON gp.name = gpp.group_id
        LEFT JOIN {perm_table} p1 ON gpp.perm_id = p1.name
        LEFT JOIN {user_perm_table} up ON u.id = up.user_id
        LEFT JOIN {perm_table} p2 ON up.perm_id = p2.name
        WHERE (gpp.allow = TRUE AND p1.name = %s)
           OR (up.allow = TRUE AND p2.name = %s)
        """

    cur.execute(query, (perm_name, perm_name))
    user_ids = cur.fetchall()

    cur.close()
    conn.close()

    return [user_id[0] for user_id in user_ids]


def project_db_execute(query, params):
    """
    Executes a PostgreSQL query and returns the result.
    :param query: The SQL query to be executed.
    :param params: A tuple of parameters to be used in the query.
    :return: The result of the query as a list of dictionaries.
    """
    conn = psycopg2.connect(
        dbname=PGS_DB,
        user=PGS_USER,
        password=PGS_PASSWORD,
        host=PGS_HOST,
        port=PGS_PORT
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    return result


def get_user_model():
    Perm = apps.get_model('account', 'Perm')
    User = apps.get_model('account', 'User')
    UserGroupPerm = apps.get_model('account', 'UserGroupPerm')
    GroupPerm = apps.get_model('account', 'GroupPerm')
    UserPerm = apps.get_model('account', 'UserPerm')
    GroupPermPerms = apps.get_model('account', 'GroupPermPerms')
    return Perm, User, UserGroupPerm, GroupPerm, UserPerm, GroupPermPerms
