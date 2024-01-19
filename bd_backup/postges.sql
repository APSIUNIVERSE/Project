--
-- PostgreSQL database dump
--

-- Dumped from database version 16.1
-- Dumped by pg_dump version 16.1

-- Started on 2024-01-09 12:57:24

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
-- TOC entry 4860 (class 1262 OID 5)
-- Name: postgres; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE postgres WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Russian_Russia.1251';


ALTER DATABASE postgres OWNER TO postgres;

\connect postgres

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
-- TOC entry 4861 (class 0 OID 0)
-- Dependencies: 4860
-- Name: DATABASE postgres; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON DATABASE postgres IS 'default administrative connection database';


--
-- TOC entry 5 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: pg_database_owner
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO pg_database_owner;

--
-- TOC entry 4862 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: pg_database_owner
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 218 (class 1259 OID 16442)
-- Name: addresses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.addresses (
    address text NOT NULL,
    city_id bigint NOT NULL,
    id bigint NOT NULL,
    number_of_checks bigint DEFAULT '-1'::integer NOT NULL
);


ALTER TABLE public.addresses OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16550)
-- Name: addresses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.addresses ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.addresses_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 220 (class 1259 OID 16456)
-- Name: base_check; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.base_check (
    zone17 text NOT NULL,
    comments text,
    data_id bigint NOT NULL,
    id bigint NOT NULL,
    "YPR_username" text NOT NULL,
    address_id bigint NOT NULL,
    "YPR_id" text NOT NULL,
    "Checker_id" text NOT NULL,
    "Checker_username" text NOT NULL,
    n integer DEFAULT 1 NOT NULL,
    ans_zones text,
    comments_inspector text
);


ALTER TABLE public.base_check OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 16549)
-- Name: base_check_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.base_check ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.base_check_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 217 (class 1259 OID 16435)
-- Name: cities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cities (
    city text NOT NULL,
    id bigint NOT NULL
);


ALTER TABLE public.cities OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16547)
-- Name: cities_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.cities ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.cities_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 219 (class 1259 OID 16449)
-- Name: dates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dates (
    data text NOT NULL,
    id bigint NOT NULL
);


ALTER TABLE public.dates OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 16546)
-- Name: dates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.dates ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.dates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 228 (class 1259 OID 16576)
-- Name: quantity; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.quantity (
    quantity bigint DEFAULT 0 NOT NULL,
    id bigint NOT NULL,
    n integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.quantity OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16489)
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    role text NOT NULL,
    id smallint NOT NULL
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16545)
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.roles ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.roles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 229 (class 1259 OID 16589)
-- Name: user_address; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_address (
    id bigint NOT NULL,
    address_id bigint NOT NULL,
    role_id bigint NOT NULL,
    city_id bigint NOT NULL,
    user_id text NOT NULL
);


ALTER TABLE public.user_address OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 16594)
-- Name: user_address_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.user_address ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.user_address_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 216 (class 1259 OID 16428)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id text NOT NULL,
    role_id smallint NOT NULL,
    id bigint NOT NULL,
    username text NOT NULL,
    condition integer DEFAULT 0 NOT NULL,
    number_of_base_checks integer DEFAULT 0 NOT NULL,
    online smallint DEFAULT 0 NOT NULL,
    base_check_id bigint
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 16543)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.users ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 4842 (class 0 OID 16442)
-- Dependencies: 218
-- Data for Name: addresses; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4844 (class 0 OID 16456)
-- Dependencies: 220
-- Data for Name: base_check; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4841 (class 0 OID 16435)
-- Dependencies: 217
-- Data for Name: cities; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4843 (class 0 OID 16449)
-- Dependencies: 219
-- Data for Name: dates; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4852 (class 0 OID 16576)
-- Dependencies: 228
-- Data for Name: quantity; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.quantity VALUES (0, 1, 1);


--
-- TOC entry 4845 (class 0 OID 16489)
-- Dependencies: 221
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.roles OVERRIDING SYSTEM VALUE VALUES ('YPR', 1);
INSERT INTO public.roles OVERRIDING SYSTEM VALUE VALUES ('Checker', 2);
INSERT INTO public.roles OVERRIDING SYSTEM VALUE VALUES ('SuperUser', 3);


--
-- TOC entry 4853 (class 0 OID 16589)
-- Dependencies: 229
-- Data for Name: user_address; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4840 (class 0 OID 16428)
-- Dependencies: 216
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4863 (class 0 OID 0)
-- Dependencies: 227
-- Name: addresses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.addresses_id_seq', 96, true);


--
-- TOC entry 4864 (class 0 OID 0)
-- Dependencies: 226
-- Name: base_check_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.base_check_id_seq', 1, false);


--
-- TOC entry 4865 (class 0 OID 0)
-- Dependencies: 225
-- Name: cities_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cities_id_seq', 83, true);


--
-- TOC entry 4866 (class 0 OID 0)
-- Dependencies: 224
-- Name: dates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.dates_id_seq', 70, true);


--
-- TOC entry 4867 (class 0 OID 0)
-- Dependencies: 223
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.roles_id_seq', 1, false);


--
-- TOC entry 4868 (class 0 OID 0)
-- Dependencies: 230
-- Name: user_address_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_address_id_seq', 18, true);


--
-- TOC entry 4869 (class 0 OID 0)
-- Dependencies: 222
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 1, false);


--
-- TOC entry 4681 (class 2606 OID 16477)
-- Name: addresses  addresses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.addresses
    ADD CONSTRAINT " addresses_pkey" PRIMARY KEY (id);


--
-- TOC entry 4685 (class 2606 OID 16516)
-- Name: base_check base_check_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.base_check
    ADD CONSTRAINT base_check_pkey PRIMARY KEY (id);


--
-- TOC entry 4679 (class 2606 OID 16473)
-- Name: cities cities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT cities_pkey PRIMARY KEY (id);


--
-- TOC entry 4683 (class 2606 OID 16480)
-- Name: dates data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dates
    ADD CONSTRAINT data_pkey PRIMARY KEY (id);


--
-- TOC entry 4689 (class 2606 OID 16582)
-- Name: quantity quantity_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quantity
    ADD CONSTRAINT quantity_pkey PRIMARY KEY (id);


--
-- TOC entry 4687 (class 2606 OID 16498)
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- TOC entry 4691 (class 2606 OID 16593)
-- Name: user_address user_address_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_address
    ADD CONSTRAINT user_address_pkey PRIMARY KEY (id);


--
-- TOC entry 4677 (class 2606 OID 16529)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4695 (class 2606 OID 16535)
-- Name: base_check address_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.base_check
    ADD CONSTRAINT address_fkey FOREIGN KEY (address_id) REFERENCES public.addresses(id) NOT VALID;


--
-- TOC entry 4692 (class 2606 OID 16584)
-- Name: users base_check_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT base_check_fkey FOREIGN KEY (base_check_id) REFERENCES public.base_check(id) NOT VALID;


--
-- TOC entry 4694 (class 2606 OID 16504)
-- Name: addresses city_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.addresses
    ADD CONSTRAINT city_fkey FOREIGN KEY (city_id) REFERENCES public.cities(id) NOT VALID;


--
-- TOC entry 4696 (class 2606 OID 16517)
-- Name: base_check data_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.base_check
    ADD CONSTRAINT data_fkey FOREIGN KEY (data_id) REFERENCES public.dates(id) NOT VALID;


--
-- TOC entry 4693 (class 2606 OID 16499)
-- Name: users role_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT role_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) NOT VALID;


-- Completed on 2024-01-09 12:57:24

--
-- PostgreSQL database dump complete
--

