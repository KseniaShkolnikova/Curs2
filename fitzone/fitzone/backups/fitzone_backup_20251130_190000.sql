--
-- PostgreSQL database dump
--

-- Dumped from database version 16.3
-- Dumped by pg_dump version 16.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: auto_add_class_payment(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.auto_add_class_payment() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_price NUMERIC;
    v_total_price NUMERIC;
BEGIN
    SELECT price INTO v_price
    FROM Classes
    WHERE id_class = NEW.class_id;

    v_total_price := v_price * NEW.amount;

    INSERT INTO Payments (subscription_id, classclient_id, price, paymentdate)
    VALUES (NULL, NEW.id_classclient, v_total_price, CURRENT_TIMESTAMP);
	
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.auto_add_class_payment() OWNER TO postgres;

--
-- Name: auto_add_payment(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.auto_add_payment() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_price NUMERIC;
BEGIN
    SELECT price INTO v_price
    FROM SubscriptionTypes
    WHERE id_subscriptiontype = NEW.subscriptiontype_id;

    INSERT INTO Payments (subscription_id, classclient_id, price, paymentdate)
    VALUES (NEW.id_subscriptions, NULL, v_price, CURRENT_TIMESTAMP);

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.auto_add_payment() OWNER TO postgres;

--
-- Name: calculate_total_revenue(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calculate_total_revenue() RETURNS numeric
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_total_revenue NUMERIC(10,2) := 0;
BEGIN
    -- Подсчёт общей суммы платежей
    SELECT COALESCE(SUM(price), 0)
    INTO v_total_revenue
    FROM Payments;

    RAISE NOTICE 'Общий доход: %', v_total_revenue;

    RETURN v_total_revenue;
END;
$$;


ALTER FUNCTION public.calculate_total_revenue() OWNER TO postgres;

--
-- Name: class_all(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.class_all() RETURNS TABLE(id_class integer, trainer_id integer, name character varying, description character varying, starttime timestamp without time zone, endtime timestamp without time zone, maxclient integer, price numeric, is_active boolean, firstname character varying, lastname character varying)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY
    SELECT c.id_class, c.trainer_id, c.name, c.description, c.starttime, c.endtime, c.maxclient, c.price, c.is_active, up.firstname, up.lastname
    FROM Classes c
    INNER JOIN UserProfiles up ON c.trainer_id = up.user_id
    WHERE c.is_active = TRUE;
END;
    $$;


ALTER FUNCTION public.class_all() OWNER TO postgres;

--
-- Name: class_create(integer, character varying, character varying, timestamp without time zone, timestamp without time zone, integer, numeric); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.class_create(p_trainer_id integer, p_name character varying, p_description character varying, p_starttime timestamp without time zone, p_endtime timestamp without time zone, p_maxclient integer, p_price numeric) RETURNS integer
    LANGUAGE plpgsql
    AS $$    
DECLARE
    new_id INTEGER;
BEGIN
    INSERT INTO Classes (trainer_id, name, description, starttime, endtime, maxclient, price)
    VALUES (p_trainer_id, p_name, p_description, p_starttime, p_endtime, p_maxclient, p_price)
    RETURNING id_class INTO new_id;
    RETURN new_id;
END;
    $$;


ALTER FUNCTION public.class_create(p_trainer_id integer, p_name character varying, p_description character varying, p_starttime timestamp without time zone, p_endtime timestamp without time zone, p_maxclient integer, p_price numeric) OWNER TO postgres;

--
-- Name: class_delete(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.class_delete(p_id_class integer) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    DELETE FROM Classes WHERE id_class = p_id_class;
END;
    $$;


ALTER FUNCTION public.class_delete(p_id_class integer) OWNER TO postgres;

--
-- Name: class_getbyid(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.class_getbyid(p_trainer_id integer) RETURNS TABLE(id_class integer, trainer_id integer, name character varying, description character varying, starttime timestamp without time zone, endtime timestamp without time zone, maxclient integer, price numeric, is_active boolean)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY SELECT c.id_class, c.trainer_id, c.name, c.description, c.starttime, c.endtime, c.maxclient, c.price, c.is_active 
                 FROM Classes c 
                 WHERE c.trainer_id = p_trainer_id AND c.is_active = TRUE;
END;
    $$;


ALTER FUNCTION public.class_getbyid(p_trainer_id integer) OWNER TO postgres;

--
-- Name: class_update(integer, integer, character varying, character varying, timestamp without time zone, timestamp without time zone, integer, numeric, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.class_update(p_id_class integer, p_trainer_id integer, p_name character varying, p_description character varying, p_starttime timestamp without time zone, p_endtime timestamp without time zone, p_maxclient integer, p_price numeric, p_is_active boolean) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    UPDATE Classes
    SET trainer_id = p_trainer_id,
        name = p_name,
        description = p_description,
        starttime = p_starttime,
        endtime = p_endtime,
        maxclient = p_maxclient,
        price = p_price,
        is_active = p_is_active
    WHERE id_class = p_id_class;
END;
    $$;


ALTER FUNCTION public.class_update(p_id_class integer, p_trainer_id integer, p_name character varying, p_description character varying, p_starttime timestamp without time zone, p_endtime timestamp without time zone, p_maxclient integer, p_price numeric, p_is_active boolean) OWNER TO postgres;

--
-- Name: classclient_create(integer, integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.classclient_create(p_class_id integer, p_user_id integer, p_amount integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$    
DECLARE
    new_id INTEGER;
BEGIN
    INSERT INTO ClassClient (class_id, user_id, amount)
    VALUES (p_class_id, p_user_id, p_amount)
    RETURNING id_classclient INTO new_id;
    RETURN new_id;
END;
    $$;


ALTER FUNCTION public.classclient_create(p_class_id integer, p_user_id integer, p_amount integer) OWNER TO postgres;

--
-- Name: classclient_delete(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.classclient_delete(p_id_classclient integer) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    DELETE FROM ClassClient WHERE id_classclient = p_id_classclient;
END;
    $$;


ALTER FUNCTION public.classclient_delete(p_id_classclient integer) OWNER TO postgres;

--
-- Name: classclient_getbyid(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.classclient_getbyid(p_class_id integer) RETURNS TABLE(id_classclient integer, class_id integer, user_id integer, amount integer, is_active boolean, firstname character varying, lastname character varying, email character varying)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY
    SELECT cc.id_classclient, cc.class_id, cc.user_id, cc.amount, cc.is_active, up.firstname, up.lastname, u.email
    FROM ClassClient cc
    INNER JOIN Users u ON cc.user_id = u.id_user
    INNER JOIN UserProfiles up ON u.id_user = up.user_id
    WHERE cc.class_id = p_class_id AND cc.is_active = TRUE;
END;
    $$;


ALTER FUNCTION public.classclient_getbyid(p_class_id integer) OWNER TO postgres;

--
-- Name: classclient_update(integer, integer, integer, integer, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.classclient_update(p_id_classclient integer, p_class_id integer, p_user_id integer, p_amount integer, p_is_active boolean) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    UPDATE ClassClient
    SET class_id = p_class_id,
        user_id = p_user_id,
        amount = p_amount,
        is_active = p_is_active
    WHERE id_classclient = p_id_classclient;
END;
    $$;


ALTER FUNCTION public.classclient_update(p_id_classclient integer, p_class_id integer, p_user_id integer, p_amount integer, p_is_active boolean) OWNER TO postgres;

--
-- Name: deactivate_subscriptions(); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.deactivate_subscriptions()
    LANGUAGE plpgsql
    AS $$    
DECLARE
    v_subscription RECORD;
BEGIN
    FOR v_subscription IN
        SELECT s.id_subscriptions, s.startdate, st.durationdays
        FROM Subscriptions s
        JOIN SubscriptionTypes st ON s.subscriptiontype_id = st.id_subscriptiontype
        WHERE s.is_active = TRUE
    LOOP
        IF CURRENT_DATE > v_subscription.startdate + v_subscription.durationdays THEN
            UPDATE Subscriptions
            SET is_active = FALSE
            WHERE id_subscriptions = v_subscription.id_subscriptions;
        END IF;
    END LOOP;

    RAISE NOTICE 'Деактивация выполнена успешно';
END;
    $$;


ALTER PROCEDURE public.deactivate_subscriptions() OWNER TO postgres;

--
-- Name: deduct_class_amount(); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.deduct_class_amount()
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_record RECORD;
BEGIN
    FOR v_record IN
        SELECT cc.id_classclient, cc.user_id, cc.amount, c.starttime
        FROM ClassClient cc
        JOIN Classes c ON cc.class_id = c.id_class
        WHERE cc.is_active = TRUE AND cc.amount > 0
    LOOP
        IF CURRENT_TIMESTAMP >= v_record.starttime THEN
            UPDATE ClassClient
            SET amount = amount - 1
            WHERE id_classclient = v_record.id_classclient;

            IF (SELECT amount FROM ClassClient WHERE id_classclient = v_record.id_classclient) = 0 THEN
                UPDATE ClassClient
                SET is_active = FALSE
                WHERE id_classclient = v_record.id_classclient;
            END IF;
        END IF;
    END LOOP;

    RAISE NOTICE 'Списание занятий выполнено успешно';
END;
$$;


ALTER PROCEDURE public.deduct_class_amount() OWNER TO postgres;

--
-- Name: get_available_classes(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_available_classes() RETURNS TABLE(id_class integer, name character varying, description character varying, starttime timestamp without time zone, endtime timestamp without time zone, maxclient integer, enrolled_count bigint, available_slots bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT c.id_class, c.name, c.description, c.starttime, c.endtime,
           c.maxclient,
           COUNT(cc.id_classclient) AS enrolled_count,
           (c.maxclient - COUNT(cc.id_classclient)) AS available_slots
    FROM Classes c
    LEFT JOIN ClassClient cc ON c.id_class = cc.class_id AND cc.is_active = TRUE
    WHERE c.is_active = TRUE
      AND c.starttime > CURRENT_TIMESTAMP
    GROUP BY c.id_class, c.name, c.description, c.starttime, c.endtime, c.maxclient
    HAVING COUNT(cc.id_classclient) < c.maxclient
    ORDER BY c.starttime;
END;
$$;


ALTER FUNCTION public.get_available_classes() OWNER TO postgres;

--
-- Name: get_trainer_classes(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_trainer_classes(p_trainer_id integer) RETURNS TABLE(id_class integer, name character varying, description character varying, starttime timestamp without time zone, endtime timestamp without time zone, maxclient integer, price numeric, enrolled_count bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT c.id_class, c.name, c.description, c.starttime, c.endtime,
           c.maxclient, c.price,
           COUNT(cc.id_classclient) AS enrolled_count
    FROM Classes c
    LEFT JOIN ClassClient cc ON c.id_class = cc.class_id AND cc.is_active = TRUE
    WHERE c.trainer_id = p_trainer_id AND c.is_active = TRUE
    GROUP BY c.id_class, c.name, c.description, c.starttime, c.endtime, c.maxclient, c.price
    ORDER BY c.starttime;
END;
$$;


ALTER FUNCTION public.get_trainer_classes(p_trainer_id integer) OWNER TO postgres;

--
-- Name: log_action(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_action() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_id INTEGER;
    v_action_text TEXT;
BEGIN
    SELECT id_user INTO v_user_id
    FROM Users
    WHERE email = current_user
    LIMIT 1;

    IF NOT FOUND THEN
        v_user_id := NULL;
    END IF;

    IF TG_OP = 'INSERT' THEN
        v_action_text := format('%s Добавлена запись: (%s)', TG_TABLE_NAME, row_to_json(NEW)::text);
    ELSIF TG_OP = 'UPDATE' THEN
        v_action_text := format('%s Обновление записи: До: (%s), После: (%s)', TG_TABLE_NAME, row_to_json(OLD)::text, row_to_json(NEW)::text);
    ELSIF TG_OP = 'DELETE' THEN
        v_action_text := format('%s Удалена запись: (%s)', TG_TABLE_NAME, row_to_json(OLD)::text);
    END IF;

    INSERT INTO UserActionsLog (user_id, action, actiondate)
    VALUES (v_user_id, v_action_text, CURRENT_TIMESTAMP);

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$;


ALTER FUNCTION public.log_action() OWNER TO postgres;

--
-- Name: reschedule_class(integer, timestamp without time zone, timestamp without time zone, integer); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.reschedule_class(IN p_class_id integer, IN p_new_starttime timestamp without time zone, IN p_new_endtime timestamp without time zone, IN p_admin_id integer)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_conflict_count INTEGER; 
    v_trainer_id INTEGER; 
    v_old_starttime TIMESTAMP;
    v_old_endtime TIMESTAMP; 
BEGIN
    SELECT trainer_id, starttime, endtime
    INTO v_trainer_id, v_old_starttime, v_old_endtime
    FROM Classes
    WHERE id_class = p_class_id AND is_active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Занятие с ID % не найдено или не активно', p_class_id;
    END IF;

    IF p_new_starttime < CURRENT_TIMESTAMP THEN
        RAISE EXCEPTION 'Новое время начала % уже прошло', p_new_starttime;
    END IF;

    IF p_new_endtime <= p_new_starttime THEN
        RAISE EXCEPTION 'Время окончания % должно быть позже времени начала %', p_new_endtime, p_new_starttime;
    END IF;

    SELECT COUNT(*)
    INTO v_conflict_count
    FROM ClassClient cc
    JOIN Classes c ON cc.class_id = c.id_class
    WHERE cc.class_id != p_class_id
      AND cc.is_active = TRUE
      AND cc.user_id IN (
          SELECT user_id
          FROM ClassClient
          WHERE class_id = p_class_id AND is_active = TRUE
      )
      AND (
          (c.starttime <= p_new_endtime + INTERVAL '10 minutes' AND c.endtime >= p_new_starttime - INTERVAL '10 minutes')
      );

    IF v_conflict_count > 0 THEN
        RAISE EXCEPTION 'Конфликт расписания для % клиентов с новым временем %–%', v_conflict_count, p_new_starttime, p_new_endtime;
    END IF;

    UPDATE Classes
    SET starttime = p_new_starttime,
        endtime = p_new_endtime
    WHERE id_class = p_class_id;

    UPDATE ClassClient
    SET is_active = TRUE
    WHERE class_id = p_class_id AND is_active = TRUE;
END;
$$;


ALTER PROCEDURE public.reschedule_class(IN p_class_id integer, IN p_new_starttime timestamp without time zone, IN p_new_endtime timestamp without time zone, IN p_admin_id integer) OWNER TO postgres;

--
-- Name: role_all(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.role_all() RETURNS TABLE(id_role integer, role_name character varying)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY SELECT r.id_role, r.role_name FROM Roles r;
END;
    $$;


ALTER FUNCTION public.role_all() OWNER TO postgres;

--
-- Name: role_create(character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.role_create(p_role_name character varying) RETURNS integer
    LANGUAGE plpgsql
    AS $$    
DECLARE
    new_id INTEGER;
BEGIN
    INSERT INTO Roles (role_name) VALUES (p_role_name)
    RETURNING id_role INTO new_id;
    RETURN new_id;
END;
    $$;


ALTER FUNCTION public.role_create(p_role_name character varying) OWNER TO postgres;

--
-- Name: role_delete(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.role_delete(p_id_role integer) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    DELETE FROM Roles WHERE id_role = p_id_role;
END;
    $$;


ALTER FUNCTION public.role_delete(p_id_role integer) OWNER TO postgres;

--
-- Name: role_getbyid(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.role_getbyid(p_id_role integer) RETURNS TABLE(id_role integer, role_name character varying)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY SELECT r.id_role, r.role_name FROM Roles r WHERE r.id_role = p_id_role;
END;
    $$;


ALTER FUNCTION public.role_getbyid(p_id_role integer) OWNER TO postgres;

--
-- Name: role_update(integer, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.role_update(p_id_role integer, p_role_name character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    UPDATE Roles SET role_name = p_role_name WHERE id_role = p_id_role;
END;
    $$;


ALTER FUNCTION public.role_update(p_id_role integer, p_role_name character varying) OWNER TO postgres;

--
-- Name: subscription_all(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.subscription_all() RETURNS TABLE(id_subscriptions integer, user_id integer, subscriptiontype_id integer, startdate date, is_active boolean, email character varying, subscriptionname character varying)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY
    SELECT s.id_subscriptions, s.user_id, s.subscriptiontype_id, s.startdate, s.is_active, u.email, st.name AS subscriptionname
    FROM Subscriptions s
    INNER JOIN Users u ON s.user_id = u.id_user
    INNER JOIN SubscriptionTypes st ON s.subscriptiontype_id = st.id_subscriptiontype;
END;
    $$;


ALTER FUNCTION public.subscription_all() OWNER TO postgres;

--
-- Name: subscription_create(integer, integer, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.subscription_create(p_user_id integer, p_subscriptiontype_id integer, p_startdate date) RETURNS integer
    LANGUAGE plpgsql
    AS $$    
DECLARE
    new_id INTEGER;
BEGIN
    INSERT INTO Subscriptions (user_id, subscriptiontype_id, startdate)
    VALUES (p_user_id, p_subscriptiontype_id, p_startdate)
    RETURNING id_subscriptions INTO new_id;
    RETURN new_id;
END;
    $$;


ALTER FUNCTION public.subscription_create(p_user_id integer, p_subscriptiontype_id integer, p_startdate date) OWNER TO postgres;

--
-- Name: subscription_delete(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.subscription_delete(p_id_subscriptions integer) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    DELETE FROM Subscriptions WHERE id_subscriptions = p_id_subscriptions;
END;
    $$;


ALTER FUNCTION public.subscription_delete(p_id_subscriptions integer) OWNER TO postgres;

--
-- Name: subscription_getbyid(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.subscription_getbyid(p_user_id integer) RETURNS TABLE(id_subscriptions integer, user_id integer, subscriptiontype_id integer, startdate date, is_active boolean, name character varying, price numeric, durationdays integer)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY
    SELECT s.id_subscriptions, s.user_id, s.subscriptiontype_id, s.startdate, s.is_active, st.name, st.price, st.durationdays
    FROM Subscriptions s
    INNER JOIN SubscriptionTypes st ON s.subscriptiontype_id = st.id_subscriptiontype
    WHERE s.user_id = p_user_id AND s.is_active = TRUE;
END;
    $$;


ALTER FUNCTION public.subscription_getbyid(p_user_id integer) OWNER TO postgres;

--
-- Name: subscription_update(integer, integer, integer, date, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.subscription_update(p_id_subscriptions integer, p_user_id integer, p_subscriptiontype_id integer, p_startdate date, p_is_active boolean) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    UPDATE Subscriptions
    SET user_id = p_user_id,
        subscriptiontype_id = p_subscriptiontype_id,
        startdate = p_startdate,
        is_active = p_is_active
    WHERE id_subscriptions = p_id_subscriptions;
END;
    $$;


ALTER FUNCTION public.subscription_update(p_id_subscriptions integer, p_user_id integer, p_subscriptiontype_id integer, p_startdate date, p_is_active boolean) OWNER TO postgres;

--
-- Name: subscriptiontype_all(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.subscriptiontype_all() RETURNS TABLE(id_subscriptiontype integer, name character varying, description character varying, price numeric, durationdays integer)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY SELECT st.id_subscriptiontype, st.name, st.description, st.price, st.durationdays FROM SubscriptionTypes st;
END;
    $$;


ALTER FUNCTION public.subscriptiontype_all() OWNER TO postgres;

--
-- Name: subscriptiontype_create(character varying, character varying, numeric, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.subscriptiontype_create(p_name character varying, p_description character varying, p_price numeric, p_durationdays integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$    
DECLARE
    new_id INTEGER;
BEGIN
    INSERT INTO SubscriptionTypes (name, description, price, durationdays)
    VALUES (p_name, p_description, p_price, p_durationdays)
    RETURNING id_subscriptiontype INTO new_id;
    RETURN new_id;
END;
    $$;


ALTER FUNCTION public.subscriptiontype_create(p_name character varying, p_description character varying, p_price numeric, p_durationdays integer) OWNER TO postgres;

--
-- Name: subscriptiontype_delete(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.subscriptiontype_delete(p_id_subscriptiontype integer) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    DELETE FROM SubscriptionTypes WHERE id_subscriptiontype = p_id_subscriptiontype;
END;
    $$;


ALTER FUNCTION public.subscriptiontype_delete(p_id_subscriptiontype integer) OWNER TO postgres;

--
-- Name: subscriptiontype_getbyid(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.subscriptiontype_getbyid(p_id_subscriptiontype integer) RETURNS TABLE(id_subscriptiontype integer, name character varying, description character varying, price numeric, durationdays integer)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY SELECT st.id_subscriptiontype, st.name, st.description, st.price, st.durationdays FROM SubscriptionTypes st WHERE st.id_subscriptiontype = p_id_subscriptiontype;
END;
    $$;


ALTER FUNCTION public.subscriptiontype_getbyid(p_id_subscriptiontype integer) OWNER TO postgres;

--
-- Name: subscriptiontype_update(integer, character varying, character varying, numeric, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.subscriptiontype_update(p_id_subscriptiontype integer, p_name character varying, p_description character varying, p_price numeric, p_durationdays integer) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    UPDATE SubscriptionTypes
    SET name = p_name,
        description = p_description,
        price = p_price,
        durationdays = p_durationdays
    WHERE id_subscriptiontype = p_id_subscriptiontype;
END;
    $$;


ALTER FUNCTION public.subscriptiontype_update(p_id_subscriptiontype integer, p_name character varying, p_description character varying, p_price numeric, p_durationdays integer) OWNER TO postgres;

--
-- Name: trainingplan_all(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trainingplan_all() RETURNS TABLE(id_trainingplan integer, trainer_id integer, client_id integer, name character varying, description character varying, is_active boolean, trainerfirstname character varying, trainerlastname character varying, clientfirstname character varying, clientlastname character varying)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY
    SELECT tp.id_trainingplan, tp.trainer_id, tp.client_id, tp.name, tp.description, tp.is_active,
           tup.firstname AS trainerfirstname,
           tup.lastname AS trainerlastname,
           cup.firstname AS clientfirstname,
           cup.lastname AS clientlastname
    FROM TrainingPlans tp
    INNER JOIN UserProfiles tup ON tp.trainer_id = tup.user_id
    INNER JOIN UserProfiles cup ON tp.client_id = cup.user_id;
END;
    $$;


ALTER FUNCTION public.trainingplan_all() OWNER TO postgres;

--
-- Name: trainingplan_create(integer, integer, character varying, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trainingplan_create(p_trainer_id integer, p_client_id integer, p_name character varying, p_description character varying) RETURNS integer
    LANGUAGE plpgsql
    AS $$    
DECLARE
    new_id INTEGER;
BEGIN
    INSERT INTO TrainingPlans (trainer_id, client_id, name, description)
    VALUES (p_trainer_id, p_client_id, p_name, p_description)
    RETURNING id_trainingplan INTO new_id;
    RETURN new_id;
END;
    $$;


ALTER FUNCTION public.trainingplan_create(p_trainer_id integer, p_client_id integer, p_name character varying, p_description character varying) OWNER TO postgres;

--
-- Name: trainingplan_delete(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trainingplan_delete(p_id_trainingplan integer) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    DELETE FROM TrainingPlans WHERE id_trainingplan = p_id_trainingplan;
END;
    $$;


ALTER FUNCTION public.trainingplan_delete(p_id_trainingplan integer) OWNER TO postgres;

--
-- Name: trainingplan_getbyid(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trainingplan_getbyid(p_client_id integer) RETURNS TABLE(id_trainingplan integer, trainer_id integer, client_id integer, name character varying, description character varying, is_active boolean, trainerfirstname character varying, trainerlastname character varying)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY
    SELECT tp.id_trainingplan, tp.trainer_id, tp.client_id, tp.name, tp.description, tp.is_active,
           tup.firstname AS trainerfirstname,
           tup.lastname AS trainerlastname
    FROM TrainingPlans tp
    INNER JOIN UserProfiles tup ON tp.trainer_id = tup.user_id
    WHERE tp.client_id = p_client_id AND tp.is_active = TRUE;
END;
    $$;


ALTER FUNCTION public.trainingplan_getbyid(p_client_id integer) OWNER TO postgres;

--
-- Name: trainingplan_update(integer, integer, integer, character varying, character varying, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trainingplan_update(p_id_trainingplan integer, p_trainer_id integer, p_client_id integer, p_name character varying, p_description character varying, p_is_active boolean) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    UPDATE TrainingPlans
    SET trainer_id = p_trainer_id,
        client_id = p_client_id,
        name = p_name,
        description = p_description,
        is_active = p_is_active
    WHERE id_trainingplan = p_id_trainingplan;
END;
    $$;


ALTER FUNCTION public.trainingplan_update(p_id_trainingplan integer, p_trainer_id integer, p_client_id integer, p_name character varying, p_description character varying, p_is_active boolean) OWNER TO postgres;

--
-- Name: user_all(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.user_all() RETURNS TABLE(id_user integer, email character varying, password_hash character varying, role_id integer, is_active boolean, passport_series character varying, passport_number character varying, date_of_issue date)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY SELECT u.id_user, u.email, u.password_hash, u.role_id, u.is_active, u.passport_series, u.passport_number, u.date_of_issue FROM Users u;
END;
    $$;


ALTER FUNCTION public.user_all() OWNER TO postgres;

--
-- Name: user_create(character varying, character varying, integer, character varying, character varying, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.user_create(p_email character varying, p_password_hash character varying, p_role_id integer, p_passport_series character varying, p_passport_number character varying, p_date_of_issue date) RETURNS integer
    LANGUAGE plpgsql
    AS $$    
DECLARE
    new_id INTEGER;
BEGIN
    INSERT INTO Users (email, password_hash, role_id, passport_series, passport_number, date_of_issue)
    VALUES (p_email, p_password_hash, p_role_id, p_passport_series, p_passport_number, p_date_of_issue)
    RETURNING id_user INTO new_id;
    RETURN new_id;
END;
    $$;


ALTER FUNCTION public.user_create(p_email character varying, p_password_hash character varying, p_role_id integer, p_passport_series character varying, p_passport_number character varying, p_date_of_issue date) OWNER TO postgres;

--
-- Name: user_delete(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.user_delete(p_id_user integer) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    DELETE FROM Users WHERE id_user = p_id_user;
END;
    $$;


ALTER FUNCTION public.user_delete(p_id_user integer) OWNER TO postgres;

--
-- Name: user_getbyid(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.user_getbyid(p_id_user integer) RETURNS TABLE(id_user integer, email character varying, password_hash character varying, role_id integer, is_active boolean, passport_series character varying, passport_number character varying, date_of_issue date)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY SELECT u.id_user, u.email, u.password_hash, u.role_id, u.is_active, u.passport_series, u.passport_number, u.date_of_issue FROM Users u WHERE u.id_user = p_id_user;
END;
    $$;


ALTER FUNCTION public.user_getbyid(p_id_user integer) OWNER TO postgres;

--
-- Name: user_update(integer, character varying, character varying, integer, boolean, character varying, character varying, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.user_update(p_id_user integer, p_email character varying, p_password_hash character varying, p_role_id integer, p_is_active boolean, p_passport_series character varying, p_passport_number character varying, p_date_of_issue date) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    UPDATE Users
    SET email = p_email,
        password_hash = p_password_hash,
        role_id = p_role_id,
        is_active = p_is_active,
        passport_series = p_passport_series,
        passport_number = p_passport_number,
        date_of_issue = p_date_of_issue
    WHERE id_user = p_id_user;
END;
    $$;


ALTER FUNCTION public.user_update(p_id_user integer, p_email character varying, p_password_hash character varying, p_role_id integer, p_is_active boolean, p_passport_series character varying, p_passport_number character varying, p_date_of_issue date) OWNER TO postgres;

--
-- Name: userprofile_all(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.userprofile_all() RETURNS TABLE(id_userprofile integer, firstname character varying, lastname character varying, middlename character varying, gender character, user_id integer, theme boolean, email character varying, role_name character varying)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY
    SELECT up.id_userprofile, up.firstname, up.lastname, up.middlename, up.gender, up.user_id, up.theme, u.email, r.role_name
    FROM UserProfiles up
    INNER JOIN Users u ON up.user_id = u.id_user
    INNER JOIN Roles r ON u.role_id = r.id_role;
END;
    $$;


ALTER FUNCTION public.userprofile_all() OWNER TO postgres;

--
-- Name: userprofile_create(character varying, character varying, character varying, character, integer, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.userprofile_create(p_firstname character varying, p_lastname character varying, p_middlename character varying, p_gender character, p_user_id integer, p_theme boolean) RETURNS integer
    LANGUAGE plpgsql
    AS $$    
DECLARE
    new_id INTEGER;
BEGIN
    INSERT INTO UserProfiles (firstname, lastname, middlename, gender, user_id, theme)
    VALUES (p_firstname, p_lastname, p_middlename, p_gender, p_user_id, p_theme)
    RETURNING id_userprofile INTO new_id;
    RETURN new_id;
END;
    $$;


ALTER FUNCTION public.userprofile_create(p_firstname character varying, p_lastname character varying, p_middlename character varying, p_gender character, p_user_id integer, p_theme boolean) OWNER TO postgres;

--
-- Name: userprofile_delete(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.userprofile_delete(p_id_userprofile integer) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    DELETE FROM UserProfiles WHERE id_userprofile = p_id_userprofile;
END;
    $$;


ALTER FUNCTION public.userprofile_delete(p_id_userprofile integer) OWNER TO postgres;

--
-- Name: userprofile_getbyid(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.userprofile_getbyid(p_user_id integer) RETURNS TABLE(id_userprofile integer, firstname character varying, lastname character varying, middlename character varying, gender character, user_id integer, theme boolean, email character varying, role_name character varying)
    LANGUAGE plpgsql
    AS $$    
BEGIN
    RETURN QUERY
    SELECT up.id_userprofile, up.firstname, up.lastname, up.middlename, up.gender, up.user_id, up.theme, u.email, r.role_name
    FROM UserProfiles up
    INNER JOIN Users u ON up.user_id = u.id_user
    INNER JOIN Roles r ON u.role_id = r.id_role
    WHERE up.user_id = p_user_id;
END;
    $$;


ALTER FUNCTION public.userprofile_getbyid(p_user_id integer) OWNER TO postgres;

--
-- Name: userprofile_update(integer, character varying, character varying, character varying, character, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.userprofile_update(p_id_userprofile integer, p_firstname character varying, p_lastname character varying, p_middlename character varying, p_gender character, p_theme boolean) RETURNS void
    LANGUAGE plpgsql
    AS $$    
BEGIN
    UPDATE UserProfiles
    SET firstname = p_firstname,
        lastname = p_lastname,
        middlename = p_middlename,
        gender = p_gender,
        theme = p_theme
    WHERE id_userprofile = p_id_userprofile;
END;
    $$;


ALTER FUNCTION public.userprofile_update(p_id_userprofile integer, p_firstname character varying, p_lastname character varying, p_middlename character varying, p_gender character, p_theme boolean) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: classclient; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.classclient (
    id_classclient integer NOT NULL,
    class_id integer NOT NULL,
    user_id integer NOT NULL,
    amount integer NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE public.classclient OWNER TO postgres;

--
-- Name: classclient_id_classclient_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.classclient_id_classclient_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.classclient_id_classclient_seq OWNER TO postgres;

--
-- Name: classclient_id_classclient_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.classclient_id_classclient_seq OWNED BY public.classclient.id_classclient;


--
-- Name: classes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.classes (
    id_class integer NOT NULL,
    trainer_id integer NOT NULL,
    name character varying NOT NULL,
    description character varying NOT NULL,
    starttime timestamp without time zone NOT NULL,
    endtime timestamp without time zone NOT NULL,
    maxclient integer NOT NULL,
    price numeric(10,2) NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE public.classes OWNER TO postgres;

--
-- Name: userprofiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.userprofiles (
    id_userprofile integer NOT NULL,
    firstname character varying,
    lastname character varying,
    middlename character varying,
    gender character(1),
    user_id integer NOT NULL,
    theme boolean DEFAULT false NOT NULL
);


ALTER TABLE public.userprofiles OWNER TO postgres;

--
-- Name: classclient_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.classclient_view AS
 SELECT c.name AS "Название занятия",
    (((((client.firstname)::text || ' '::text) || (client.lastname)::text) || ' '::text) || (COALESCE(client.middlename, ''::character varying))::text) AS "ФИО клиента",
    cc.amount AS "Количество занятий",
        CASE
            WHEN (cc.is_active = true) THEN 'Активен'::text
            WHEN (cc.is_active = false) THEN 'Деактивирован'::text
            ELSE NULL::text
        END AS "Статус"
   FROM ((public.classclient cc
     JOIN public.classes c ON ((cc.class_id = c.id_class)))
     JOIN public.userprofiles client ON ((cc.user_id = client.user_id)));


ALTER VIEW public.classclient_view OWNER TO postgres;

--
-- Name: classes_id_class_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.classes_id_class_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.classes_id_class_seq OWNER TO postgres;

--
-- Name: classes_id_class_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.classes_id_class_seq OWNED BY public.classes.id_class;


--
-- Name: classes_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.classes_view AS
 SELECT (((((trainer.firstname)::text || ' '::text) || (trainer.lastname)::text) || ' '::text) || (COALESCE(trainer.middlename, ''::character varying))::text) AS "ФИО тренера",
    c.name AS "Название",
    c.description AS "Описание",
    (to_char(c.starttime, 'DD Month YYYY с HH24:MI до '::text) || to_char(c.endtime, 'HH24:MI'::text)) AS "Время занятия",
    c.maxclient AS "Макс. клиентов",
    concat(c.price, ' руб') AS "Цена",
        CASE
            WHEN (c.is_active = true) THEN 'Активен'::text
            WHEN (c.is_active = false) THEN 'Деактивирован'::text
            ELSE NULL::text
        END AS "Статус"
   FROM (public.classes c
     JOIN public.userprofiles trainer ON ((c.trainer_id = trainer.user_id)));


ALTER VIEW public.classes_view OWNER TO postgres;

--
-- Name: payments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payments (
    id_payment integer NOT NULL,
    subscription_id integer,
    classclient_id integer,
    price numeric(10,2) NOT NULL,
    paymentdate timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT check_payment_type CHECK ((((subscription_id IS NOT NULL) AND (classclient_id IS NULL)) OR ((subscription_id IS NULL) AND (classclient_id IS NOT NULL))))
);


ALTER TABLE public.payments OWNER TO postgres;

--
-- Name: payments_id_payment_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.payments_id_payment_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payments_id_payment_seq OWNER TO postgres;

--
-- Name: payments_id_payment_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.payments_id_payment_seq OWNED BY public.payments.id_payment;


--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.subscriptions (
    id_subscriptions integer NOT NULL,
    user_id integer NOT NULL,
    subscriptiontype_id integer NOT NULL,
    startdate date NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE public.subscriptions OWNER TO postgres;

--
-- Name: subscriptiontypes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.subscriptiontypes (
    id_subscriptiontype integer NOT NULL,
    name character varying NOT NULL,
    description character varying,
    price numeric(10,2) NOT NULL,
    durationdays integer NOT NULL
);


ALTER TABLE public.subscriptiontypes OWNER TO postgres;

--
-- Name: payments_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.payments_view AS
 SELECT
        CASE
            WHEN (p.subscription_id IS NOT NULL) THEN concat('Абонмент: ', st.name)
            ELSE concat('Занятие: ', c.name)
        END AS "Название абонемента/занятия",
    concat(p.price, ' руб') AS "Сумма оплаты",
    to_char(p.paymentdate, 'DD Month YYYY HH24:MI:SS'::text) AS "Дата платежа"
   FROM ((((public.payments p
     LEFT JOIN public.subscriptions s ON ((p.subscription_id = s.id_subscriptions)))
     LEFT JOIN public.subscriptiontypes st ON ((s.subscriptiontype_id = st.id_subscriptiontype)))
     LEFT JOIN public.classclient cc ON ((p.classclient_id = cc.id_classclient)))
     LEFT JOIN public.classes c ON ((cc.class_id = c.id_class)));


ALTER VIEW public.payments_view OWNER TO postgres;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    id_role integer NOT NULL,
    role_name character varying NOT NULL
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- Name: roles_id_role_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roles_id_role_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_role_seq OWNER TO postgres;

--
-- Name: roles_id_role_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roles_id_role_seq OWNED BY public.roles.id_role;


--
-- Name: subscriptions_id_subscriptions_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.subscriptions_id_subscriptions_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.subscriptions_id_subscriptions_seq OWNER TO postgres;

--
-- Name: subscriptions_id_subscriptions_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.subscriptions_id_subscriptions_seq OWNED BY public.subscriptions.id_subscriptions;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id_user integer NOT NULL,
    email character varying NOT NULL,
    password_hash character varying NOT NULL,
    role_id integer NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    passport_series character varying(4),
    passport_number character varying(6),
    date_of_issue date,
    CONSTRAINT users_passport_number_check CHECK (((passport_number)::text ~ '^[0-9]{6}$'::text)),
    CONSTRAINT users_passport_series_check CHECK (((passport_series)::text ~ '^[0-9]{4}$'::text))
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: subscriptions_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.subscriptions_view AS
 SELECT u.email AS "Почта",
    st.name AS "Название абонемента",
    to_char((s.startdate)::timestamp with time zone, 'DD Month YYYY'::text) AS "Дата начала",
    to_char(((s.startdate + st.durationdays))::timestamp with time zone, 'DD Month YYYY'::text) AS "Дата окончания",
        CASE
            WHEN (s.is_active = true) THEN 'Активен'::text
            WHEN (s.is_active = false) THEN 'Деактивирован'::text
            ELSE NULL::text
        END AS "Статус",
        CASE
            WHEN (((s.startdate + st.durationdays) - CURRENT_DATE) > 0) THEN (((s.startdate + st.durationdays) - CURRENT_DATE) || ' дней'::text)
            ELSE 'Истёк'::text
        END AS "Осталось дней"
   FROM ((public.subscriptions s
     JOIN public.users u ON ((s.user_id = u.id_user)))
     JOIN public.subscriptiontypes st ON ((s.subscriptiontype_id = st.id_subscriptiontype)));


ALTER VIEW public.subscriptions_view OWNER TO postgres;

--
-- Name: subscriptiontypes_id_subscriptiontype_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.subscriptiontypes_id_subscriptiontype_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.subscriptiontypes_id_subscriptiontype_seq OWNER TO postgres;

--
-- Name: subscriptiontypes_id_subscriptiontype_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.subscriptiontypes_id_subscriptiontype_seq OWNED BY public.subscriptiontypes.id_subscriptiontype;


--
-- Name: subscriptiontypes_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.subscriptiontypes_view AS
 SELECT name AS "Название",
    description AS "Описание",
    concat(price, ' руб') AS "Цена",
    concat(durationdays, ' дней') AS "Длительность"
   FROM public.subscriptiontypes;


ALTER VIEW public.subscriptiontypes_view OWNER TO postgres;

--
-- Name: trainingplans; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.trainingplans (
    id_trainingplan integer NOT NULL,
    trainer_id integer NOT NULL,
    client_id integer NOT NULL,
    name character varying NOT NULL,
    description character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE public.trainingplans OWNER TO postgres;

--
-- Name: trainingplans_id_trainingplan_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.trainingplans_id_trainingplan_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.trainingplans_id_trainingplan_seq OWNER TO postgres;

--
-- Name: trainingplans_id_trainingplan_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.trainingplans_id_trainingplan_seq OWNED BY public.trainingplans.id_trainingplan;


--
-- Name: trainingplans_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.trainingplans_view AS
 SELECT (((((trainer.firstname)::text || ' '::text) || (trainer.lastname)::text) || ' '::text) || (COALESCE(trainer.middlename, ''::character varying))::text) AS "ФИО тренера",
    (((((client.firstname)::text || ' '::text) || (client.lastname)::text) || ' '::text) || (COALESCE(client.middlename, ''::character varying))::text) AS "ФИО клиента",
    tp.name AS "Название плана",
    tp.description AS "Описание",
        CASE
            WHEN (tp.is_active = true) THEN 'Активен'::text
            WHEN (tp.is_active = false) THEN 'Деактивирован'::text
            ELSE NULL::text
        END AS "Статус"
   FROM ((public.trainingplans tp
     JOIN public.userprofiles trainer ON ((tp.trainer_id = trainer.user_id)))
     JOIN public.userprofiles client ON ((tp.client_id = client.user_id)));


ALTER VIEW public.trainingplans_view OWNER TO postgres;

--
-- Name: useractionslog; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.useractionslog (
    id_useractionlog integer NOT NULL,
    user_id integer,
    action character varying NOT NULL,
    actiondate timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.useractionslog OWNER TO postgres;

--
-- Name: useractionslog_id_useractionlog_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.useractionslog_id_useractionlog_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.useractionslog_id_useractionlog_seq OWNER TO postgres;

--
-- Name: useractionslog_id_useractionlog_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.useractionslog_id_useractionlog_seq OWNED BY public.useractionslog.id_useractionlog;


--
-- Name: useractionslog_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.useractionslog_view AS
 SELECT u.email AS "Почта",
    ual.action AS "Действие",
    to_char(ual.actiondate, 'DD Month YYYY HH24:MI:SS'::text) AS "Дата и время"
   FROM (public.useractionslog ual
     LEFT JOIN public.users u ON ((ual.user_id = u.id_user)));


ALTER VIEW public.useractionslog_view OWNER TO postgres;

--
-- Name: userprofiles_id_userprofile_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.userprofiles_id_userprofile_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.userprofiles_id_userprofile_seq OWNER TO postgres;

--
-- Name: userprofiles_id_userprofile_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.userprofiles_id_userprofile_seq OWNED BY public.userprofiles.id_userprofile;


--
-- Name: userprofiles_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.userprofiles_view AS
 SELECT (((((up.firstname)::text || ' '::text) || (up.lastname)::text) || ' '::text) || (COALESCE(up.middlename, ''::character varying))::text) AS "ФИО",
        CASE
            WHEN (up.gender = 'M'::bpchar) THEN 'Мужской'::text
            WHEN (up.gender = 'F'::bpchar) THEN 'Женский'::text
            ELSE 'Не указан'::text
        END AS "Пол",
    u.email AS "Email пользователя",
        CASE
            WHEN (up.theme = true) THEN 'Тёмная'::text
            ELSE 'Светлая'::text
        END AS "Тема интерфейса"
   FROM (public.userprofiles up
     JOIN public.users u ON ((up.user_id = u.id_user)));


ALTER VIEW public.userprofiles_view OWNER TO postgres;

--
-- Name: users_id_user_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_user_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_user_seq OWNER TO postgres;

--
-- Name: users_id_user_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_user_seq OWNED BY public.users.id_user;


--
-- Name: users_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.users_view AS
 SELECT u.email AS "Почта",
    r.role_name AS "Роль",
        CASE
            WHEN (u.is_active = true) THEN 'Активен'::text
            WHEN (u.is_active = false) THEN 'Деактивирован'::text
            ELSE NULL::text
        END AS "Статус",
    u.passport_series AS "Серия паспорта",
    u.passport_number AS "Номер паспорта",
    to_char((u.date_of_issue)::timestamp with time zone, 'DD Month YYYY'::text) AS "Дата выдачи паспорта"
   FROM (public.users u
     JOIN public.roles r ON ((u.role_id = r.id_role)));


ALTER VIEW public.users_view OWNER TO postgres;

--
-- Name: classclient id_classclient; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classclient ALTER COLUMN id_classclient SET DEFAULT nextval('public.classclient_id_classclient_seq'::regclass);


--
-- Name: classes id_class; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classes ALTER COLUMN id_class SET DEFAULT nextval('public.classes_id_class_seq'::regclass);


--
-- Name: payments id_payment; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments ALTER COLUMN id_payment SET DEFAULT nextval('public.payments_id_payment_seq'::regclass);


--
-- Name: roles id_role; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN id_role SET DEFAULT nextval('public.roles_id_role_seq'::regclass);


--
-- Name: subscriptions id_subscriptions; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscriptions ALTER COLUMN id_subscriptions SET DEFAULT nextval('public.subscriptions_id_subscriptions_seq'::regclass);


--
-- Name: subscriptiontypes id_subscriptiontype; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscriptiontypes ALTER COLUMN id_subscriptiontype SET DEFAULT nextval('public.subscriptiontypes_id_subscriptiontype_seq'::regclass);


--
-- Name: trainingplans id_trainingplan; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trainingplans ALTER COLUMN id_trainingplan SET DEFAULT nextval('public.trainingplans_id_trainingplan_seq'::regclass);


--
-- Name: useractionslog id_useractionlog; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.useractionslog ALTER COLUMN id_useractionlog SET DEFAULT nextval('public.useractionslog_id_useractionlog_seq'::regclass);


--
-- Name: userprofiles id_userprofile; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userprofiles ALTER COLUMN id_userprofile SET DEFAULT nextval('public.userprofiles_id_userprofile_seq'::regclass);


--
-- Name: users id_user; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id_user SET DEFAULT nextval('public.users_id_user_seq'::regclass);


--
-- Data for Name: classclient; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.classclient (id_classclient, class_id, user_id, amount, is_active) FROM stdin;
1	1	4	0	f
2	2	4	0	f
\.


--
-- Data for Name: classes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.classes (id_class, trainer_id, name, description, starttime, endtime, maxclient, price, is_active) FROM stdin;
2	1	Силовая	Силовая тренировка для среднего уровня	2025-09-15 17:00:00	2025-09-15 18:00:00	8	2000.00	t
1	1	Йога	Утро йоги для начинающих	2025-10-06 14:00:00	2025-10-06 15:00:00	10	1500.00	t
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payments (id_payment, subscription_id, classclient_id, price, paymentdate) FROM stdin;
1	1	\N	5999.00	2025-10-05 16:10:09.377469
2	\N	1	1500.00	2025-10-05 16:10:09.377469
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles (id_role, role_name) FROM stdin;
1	Тренерккк
2	Системный администратор
3	Менеджер по продажам
4	Клиент
\.


--
-- Data for Name: subscriptions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.subscriptions (id_subscriptions, user_id, subscriptiontype_id, startdate, is_active) FROM stdin;
1	4	1	2025-09-01	f
2	5	2	2025-09-01	f
\.


--
-- Data for Name: subscriptiontypes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.subscriptiontypes (id_subscriptiontype, name, description, price, durationdays) FROM stdin;
1	Базовая	Подписка на месяц базовая	5999.00	30
2	Премиум	Подписка на месяц премиум	9999.00	30
\.


--
-- Data for Name: trainingplans; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.trainingplans (id_trainingplan, trainer_id, client_id, name, description, is_active) FROM stdin;
1	1	4	Силовая тренировка	Тренировка на силу 3 раза в неделю	t
2	1	5	Кардио	Кардио 5 раз в неделю	t
\.


--
-- Data for Name: useractionslog; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.useractionslog (id_useractionlog, user_id, action, actiondate) FROM stdin;
1	\N	classes Обновление записи: До: ({"id_class":1,"trainer_id":1,"name":"Йога","description":"Утро йоги для начинающих","starttime":"2025-09-14T09:00:00","endtime":"2025-09-14T10:00:00","maxclient":10,"price":1500.00,"is_active":true}), После: ({"id_class":1,"trainer_id":1,"name":"Йога","description":"Утро йоги для начинающих","starttime":"2025-10-06T14:00:00","endtime":"2025-10-06T15:00:00","maxclient":10,"price":1500.00,"is_active":true})	2025-10-05 16:10:09.377469
2	\N	roles Добавлена запись: ({"id_role":5,"role_name":"Тестовая роль"})	2025-10-05 16:10:09.377469
3	\N	roles Обновление записи: До: ({"id_role":5,"role_name":"Тестовая роль"}), После: ({"id_role":5,"role_name":"Обновлённая роль"})	2025-10-05 16:10:09.377469
4	\N	roles Удалена запись: ({"id_role":5,"role_name":"Обновлённая роль"})	2025-10-05 16:10:09.377469
\.


--
-- Data for Name: userprofiles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.userprofiles (id_userprofile, firstname, lastname, middlename, gender, user_id, theme) FROM stdin;
1	Иван	Петров	Алексеевич	M	1	f
2	Елена	Сидорова	\N	F	2	t
3	Алексей	Иванов	\N	M	3	f
4	Мария	Кузнецова	Сергеевна	F	4	t
5	Петр	Соколов	\N	M	5	f
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id_user, email, password_hash, role_id, is_active, passport_series, passport_number, date_of_issue) FROM stdin;
1	trainer@example.com	hashed_password_1	1	t	1234	123456	2025-01-01
2	admin@example.com	hashed_password_2	2	t	2345	234567	2025-01-01
3	sales@example.com	hashed_password_3	3	t	3456	345678	2025-01-01
4	client1@example.com	hashed_password_4	4	t	4567	456789	2025-01-01
5	client2@example.com	hashed_password_5	4	t	5678	567890	2025-01-01
\.


--
-- Name: classclient_id_classclient_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.classclient_id_classclient_seq', 2, true);


--
-- Name: classes_id_class_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.classes_id_class_seq', 2, true);


--
-- Name: payments_id_payment_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payments_id_payment_seq', 2, true);


--
-- Name: roles_id_role_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.roles_id_role_seq', 5, true);


--
-- Name: subscriptions_id_subscriptions_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.subscriptions_id_subscriptions_seq', 2, true);


--
-- Name: subscriptiontypes_id_subscriptiontype_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.subscriptiontypes_id_subscriptiontype_seq', 2, true);


--
-- Name: trainingplans_id_trainingplan_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.trainingplans_id_trainingplan_seq', 2, true);


--
-- Name: useractionslog_id_useractionlog_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.useractionslog_id_useractionlog_seq', 4, true);


--
-- Name: userprofiles_id_userprofile_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.userprofiles_id_userprofile_seq', 5, true);


--
-- Name: users_id_user_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_user_seq', 5, true);


--
-- Name: classclient classclient_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classclient
    ADD CONSTRAINT classclient_pkey PRIMARY KEY (id_classclient);


--
-- Name: classes classes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classes
    ADD CONSTRAINT classes_pkey PRIMARY KEY (id_class);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id_payment);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id_role);


--
-- Name: roles roles_role_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_role_name_key UNIQUE (role_name);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id_subscriptions);


--
-- Name: subscriptiontypes subscriptiontypes_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscriptiontypes
    ADD CONSTRAINT subscriptiontypes_name_key UNIQUE (name);


--
-- Name: subscriptiontypes subscriptiontypes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscriptiontypes
    ADD CONSTRAINT subscriptiontypes_pkey PRIMARY KEY (id_subscriptiontype);


--
-- Name: trainingplans trainingplans_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trainingplans
    ADD CONSTRAINT trainingplans_pkey PRIMARY KEY (id_trainingplan);


--
-- Name: classclient unique_class_user; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classclient
    ADD CONSTRAINT unique_class_user UNIQUE (class_id, user_id);


--
-- Name: useractionslog useractionslog_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.useractionslog
    ADD CONSTRAINT useractionslog_pkey PRIMARY KEY (id_useractionlog);


--
-- Name: userprofiles userprofiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userprofiles
    ADD CONSTRAINT userprofiles_pkey PRIMARY KEY (id_userprofile);


--
-- Name: userprofiles userprofiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userprofiles
    ADD CONSTRAINT userprofiles_user_id_key UNIQUE (user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id_user);


--
-- Name: classclient classclient_log_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER classclient_log_trigger AFTER INSERT OR DELETE OR UPDATE ON public.classclient FOR EACH ROW EXECUTE FUNCTION public.log_action();


--
-- Name: classclient classclient_payment_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER classclient_payment_trigger AFTER INSERT ON public.classclient FOR EACH ROW EXECUTE FUNCTION public.auto_add_class_payment();


--
-- Name: classes classes_log_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER classes_log_trigger AFTER INSERT OR DELETE OR UPDATE ON public.classes FOR EACH ROW EXECUTE FUNCTION public.log_action();


--
-- Name: payments payments_log_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER payments_log_trigger AFTER INSERT OR DELETE OR UPDATE ON public.payments FOR EACH ROW EXECUTE FUNCTION public.log_action();


--
-- Name: roles roles_log_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER roles_log_trigger AFTER INSERT OR DELETE OR UPDATE ON public.roles FOR EACH ROW EXECUTE FUNCTION public.log_action();


--
-- Name: subscriptions subscriptions_log_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER subscriptions_log_trigger AFTER INSERT OR DELETE OR UPDATE ON public.subscriptions FOR EACH ROW EXECUTE FUNCTION public.log_action();


--
-- Name: subscriptions subscriptions_payment_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER subscriptions_payment_trigger AFTER INSERT ON public.subscriptions FOR EACH ROW EXECUTE FUNCTION public.auto_add_payment();


--
-- Name: subscriptiontypes subscriptiontypes_log_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER subscriptiontypes_log_trigger AFTER INSERT OR DELETE OR UPDATE ON public.subscriptiontypes FOR EACH ROW EXECUTE FUNCTION public.log_action();


--
-- Name: trainingplans trainingplans_log_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trainingplans_log_trigger AFTER INSERT OR DELETE OR UPDATE ON public.trainingplans FOR EACH ROW EXECUTE FUNCTION public.log_action();


--
-- Name: userprofiles userprofiles_log_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER userprofiles_log_trigger AFTER INSERT OR DELETE OR UPDATE ON public.userprofiles FOR EACH ROW EXECUTE FUNCTION public.log_action();


--
-- Name: users users_log_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER users_log_trigger AFTER INSERT OR DELETE OR UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.log_action();


--
-- Name: classclient classclient_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classclient
    ADD CONSTRAINT classclient_class_id_fkey FOREIGN KEY (class_id) REFERENCES public.classes(id_class);


--
-- Name: classclient classclient_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classclient
    ADD CONSTRAINT classclient_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id_user);


--
-- Name: classes classes_trainer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classes
    ADD CONSTRAINT classes_trainer_id_fkey FOREIGN KEY (trainer_id) REFERENCES public.users(id_user);


--
-- Name: payments payments_classclient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_classclient_id_fkey FOREIGN KEY (classclient_id) REFERENCES public.classclient(id_classclient);


--
-- Name: payments payments_subscription_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_subscription_id_fkey FOREIGN KEY (subscription_id) REFERENCES public.subscriptions(id_subscriptions);


--
-- Name: subscriptions subscriptions_subscriptiontype_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_subscriptiontype_id_fkey FOREIGN KEY (subscriptiontype_id) REFERENCES public.subscriptiontypes(id_subscriptiontype);


--
-- Name: subscriptions subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id_user);


--
-- Name: trainingplans trainingplans_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trainingplans
    ADD CONSTRAINT trainingplans_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.users(id_user);


--
-- Name: trainingplans trainingplans_trainer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trainingplans
    ADD CONSTRAINT trainingplans_trainer_id_fkey FOREIGN KEY (trainer_id) REFERENCES public.users(id_user);


--
-- Name: useractionslog useractionslog_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.useractionslog
    ADD CONSTRAINT useractionslog_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id_user);


--
-- Name: userprofiles userprofiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userprofiles
    ADD CONSTRAINT userprofiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id_user);


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id_role);


--
-- PostgreSQL database dump complete
--

