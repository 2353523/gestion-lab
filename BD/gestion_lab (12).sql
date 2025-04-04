-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Apr 04, 2025 at 03:22 PM
-- Server version: 9.1.0
-- PHP Version: 8.3.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `gestion_lab`
--

-- --------------------------------------------------------

--
-- Table structure for table `article`
--

DROP TABLE IF EXISTS `article`;
CREATE TABLE IF NOT EXISTS `article` (
  `id_article` int NOT NULL AUTO_INCREMENT,
  `nom_article` varchar(150) NOT NULL,
  `unite_mesure` varchar(50) NOT NULL,
  `date_expiration` datetime DEFAULT NULL,
  `id_type` int NOT NULL,
  PRIMARY KEY (`id_article`),
  KEY `id_type` (`id_type`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `article`
--

INSERT INTO `article` (`id_article`, `nom_article`, `unite_mesure`, `date_expiration`, `id_type`) VALUES
(1, 'becher', 'litre', NULL, 1),
(2, 'meden', 'litre', NULL, 1),
(7, 'pipette 20mL', 'unité', '2025-04-17 00:00:00', 1),
(8, 'bêcher  50mL', 'unité', NULL, 4),
(9, 'pippet10ml', 'unité', NULL, 1),
(10, 'NaOH', 'litre', NULL, 3),
(11, 'NaOH', 'litre', NULL, 3),
(12, 'HCl ', 'litre', NULL, 2),
(13, 'clim 12', 'unité', '2026-08-13 00:00:00', 5);

-- --------------------------------------------------------

--
-- Table structure for table `categorie`
--

DROP TABLE IF EXISTS `categorie`;
CREATE TABLE IF NOT EXISTS `categorie` (
  `id_categorie` int NOT NULL AUTO_INCREMENT,
  `nom_categorie` varchar(100) NOT NULL,
  PRIMARY KEY (`id_categorie`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `categorie`
--

INSERT INTO `categorie` (`id_categorie`, `nom_categorie`) VALUES
(1, 'materiel'),
(4, 'produit'),
(5, 'machine');

-- --------------------------------------------------------

--
-- Table structure for table `laboratoire`
--

DROP TABLE IF EXISTS `laboratoire`;
CREATE TABLE IF NOT EXISTS `laboratoire` (
  `id_laboratoire` int NOT NULL AUTO_INCREMENT,
  `nom_laboratoire` varchar(50) NOT NULL,
  `capacite` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_laboratoire`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `laboratoire`
--

INSERT INTO `laboratoire` (`id_laboratoire`, `nom_laboratoire`, `capacite`) VALUES
(1, 'Laboratoire de Chimie', 5),
(2, 'labo cinetique', 8),
(5, 'Petrochimi', 10),
(6, 'labo MPG', 6),
(7, 'Labo Min', 3),
(8, 'Labo tretment thermique', 10);

-- --------------------------------------------------------

--
-- Table structure for table `ligne_recu`
--

DROP TABLE IF EXISTS `ligne_recu`;
CREATE TABLE IF NOT EXISTS `ligne_recu` (
  `id_article` int NOT NULL DEFAULT '0',
  `id_recu` int NOT NULL DEFAULT '0',
  `quantite` int NOT NULL DEFAULT '0',
  `degradation_quantite` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_article`,`id_recu`),
  KEY `id_recu` (`id_recu`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `ligne_recu`
--

INSERT INTO `ligne_recu` (`id_article`, `id_recu`, `quantite`, `degradation_quantite`) VALUES
(8, 64, 1, 0),
(8, 68, 1, 1),
(8, 70, 1, 0),
(8, 71, 1, 0),
(8, 77, 1, 0),
(8, 79, 8, 1),
(9, 78, 1, 1),
(9, 79, 1, 0),
(9, 80, 7, 1),
(10, 80, 9, 2),
(10, 81, 7, 1),
(12, 69, 1, 0),
(12, 72, 1, 0),
(12, 74, 2, 1),
(12, 75, 5, 2),
(12, 76, 2, 2),
(13, 79, 2, 1),
(13, 80, 2, 1);

-- --------------------------------------------------------

--
-- Table structure for table `matiere`
--

DROP TABLE IF EXISTS `matiere`;
CREATE TABLE IF NOT EXISTS `matiere` (
  `id_matiere` int NOT NULL AUTO_INCREMENT,
  `nom_matiere` varchar(100) NOT NULL,
  `niveau` enum('L1','L2','L3') NOT NULL,
  PRIMARY KEY (`id_matiere`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `matiere`
--

INSERT INTO `matiere` (`id_matiere`, `nom_matiere`, `niveau`) VALUES
(1, 'GCGP_41', 'L1'),
(2, 'GCGP_42', 'L3'),
(3, 'chimi cinetique', 'L1'),
(4, 'chimi', 'L3'),
(5, 'GCGP_40', 'L2'),
(6, 'GCGP_45', 'L2');

-- --------------------------------------------------------

--
-- Table structure for table `professeur`
--

DROP TABLE IF EXISTS `professeur`;
CREATE TABLE IF NOT EXISTS `professeur` (
  `id_prof` int NOT NULL AUTO_INCREMENT,
  `prenom` varchar(50) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `email` varchar(50) NOT NULL,
  `telephone` varchar(15) NOT NULL,
  PRIMARY KEY (`id_prof`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `telephone` (`telephone`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `professeur`
--

INSERT INTO `professeur` (`id_prof`, `prenom`, `nom`, `email`, `telephone`) VALUES
(3, 'yeslem', 'teghra', '23543@isme.esp.mr', '34303065'),
(4, 'a', 'a', '07@gmail.com', '00000000'),
(6, 'med', 'sidi', '23543@isme.esp.mre', '34303464'),
(7, 'Dr.ahmed', 'ahmed', 'sidahmedmeden7@gmail.com', '34303445'),
(8, 'sidahmed', 'meden', 'sidahmedmeden@gmail.com', '65323455'),
(9, 'bebouh', 'diagana', 'the9rde@gmail.com', '34304465');

-- --------------------------------------------------------

--
-- Table structure for table `recu`
--

DROP TABLE IF EXISTS `recu`;
CREATE TABLE IF NOT EXISTS `recu` (
  `id_recu` int NOT NULL AUTO_INCREMENT,
  `date_emission` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `degradation` tinyint(1) NOT NULL DEFAULT '0',
  `observations` varchar(255) DEFAULT NULL,
  `id_tp` int NOT NULL,
  `id_prof` int NOT NULL,
  PRIMARY KEY (`id_recu`),
  UNIQUE KEY `unique_tp` (`id_tp`),
  KEY `id_tp` (`id_tp`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB AUTO_INCREMENT=82 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `recu`
--

INSERT INTO `recu` (`id_recu`, `date_emission`, `degradation`, `observations`, `id_tp`, `id_prof`) VALUES
(64, '2025-03-30 03:02:08', 0, '                                                        dciiiiiiiiiiiiiiiiiiiiiiiiiiiii\r\n                        \r\n                        ', 115, 3),
(68, '2025-04-02 11:51:54', 0, '                            kk\r\n                        ', 132, 3),
(69, '2025-04-02 12:24:14', 0, 'ilya un bogoos s\'appele 43', 133, 7),
(70, '2025-04-02 12:26:05', 0, '', 134, 7),
(71, '2025-04-02 12:26:36', 0, 'ci', 135, 7),
(72, '2025-04-02 12:27:08', 0, '', 136, 7),
(74, '2025-04-02 14:11:56', 0, '', 130, 3),
(75, '2025-04-02 14:16:55', 0, '', 148, 4),
(76, '2025-04-02 14:20:03', 0, 's', 150, 4),
(77, '2025-04-02 14:25:48', 0, '', 137, 7),
(78, '2025-04-03 01:12:44', 0, 'bien passe', 164, 8),
(79, '2025-04-03 02:15:55', 0, 'siiiiiiiiiiii\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\nd\r\n\r\n\r\nd\r\n\r\n\r\n\r\nd', 161, 8),
(80, '2025-04-03 03:48:19', 0, 'siiiiiiiiii', 160, 8),
(81, '2025-04-03 04:51:26', 0, 'siii tooo', 162, 8);

-- --------------------------------------------------------

--
-- Table structure for table `stock_laboratoire`
--

DROP TABLE IF EXISTS `stock_laboratoire`;
CREATE TABLE IF NOT EXISTS `stock_laboratoire` (
  `id_lot` int NOT NULL,
  `id_laboratoire` int NOT NULL,
  `quantite` int NOT NULL,
  PRIMARY KEY (`id_lot`,`id_laboratoire`),
  KEY `id_laboratoire` (`id_laboratoire`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `stock_laboratoire`
--

INSERT INTO `stock_laboratoire` (`id_lot`, `id_laboratoire`, `quantite`) VALUES
(5, 1, 5),
(5, 5, 1),
(6, 1, 1),
(6, 5, 1),
(6, 6, 0),
(7, 1, 3),
(7, 5, 1),
(7, 6, 16),
(8, 1, 2),
(8, 2, 9),
(8, 5, 1),
(8, 6, 7),
(9, 1, 1),
(9, 5, 1),
(10, 1, 9),
(10, 5, 1),
(10, 7, 5),
(11, 2, 2),
(11, 6, 0);

-- --------------------------------------------------------

--
-- Table structure for table `stock_magasin`
--

DROP TABLE IF EXISTS `stock_magasin`;
CREATE TABLE IF NOT EXISTS `stock_magasin` (
  `id_lot` int NOT NULL AUTO_INCREMENT,
  `id_article` int NOT NULL,
  `quantite` int NOT NULL,
  `date_expiration` datetime DEFAULT NULL,
  `date_ajout` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_lot`),
  KEY `id_article` (`id_article`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `stock_magasin`
--

INSERT INTO `stock_magasin` (`id_lot`, `id_article`, `quantite`, `date_expiration`, `date_ajout`) VALUES
(5, 7, 20, '2025-04-17 00:00:00', '2025-03-24 22:31:28'),
(6, 8, 2, NULL, '2025-03-24 22:31:52'),
(7, 9, 5, NULL, '2025-03-25 01:19:39'),
(8, 10, 0, NULL, '2025-03-25 01:28:23'),
(9, 11, 20, NULL, '2025-03-25 01:43:06'),
(10, 12, 2, NULL, '2025-03-25 07:38:16'),
(11, 13, 4, '2026-08-13 00:00:00', '2025-03-26 00:33:49');

-- --------------------------------------------------------

--
-- Table structure for table `tp`
--

DROP TABLE IF EXISTS `tp`;
CREATE TABLE IF NOT EXISTS `tp` (
  `id_tp` int NOT NULL AUTO_INCREMENT,
  `nom_tp` varchar(100) NOT NULL,
  `heure_debut` datetime NOT NULL,
  `heure_fin` datetime NOT NULL,
  `annee_scolaire` varchar(9) NOT NULL,
  `id_laboratoire` int NOT NULL,
  `id_matiere` int NOT NULL,
  `id_prof` int NOT NULL,
  `recu_genere` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id_tp`),
  KEY `id_laboratoire` (`id_laboratoire`),
  KEY `id_matiere` (`id_matiere`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB AUTO_INCREMENT=168 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `tp`
--

INSERT INTO `tp` (`id_tp`, `nom_tp`, `heure_debut`, `heure_fin`, `annee_scolaire`, `id_laboratoire`, `id_matiere`, `id_prof`, `recu_genere`) VALUES
(33, 'GCGP 34', '2025-03-10 08:00:00', '2025-03-10 09:30:00', '2024-2025', 1, 1, 3, 0),
(40, 'aaa1', '2025-03-14 08:00:00', '2025-03-14 09:30:00', '2024-2025', 5, 3, 4, 0),
(41, 'aaa1', '2025-03-14 09:45:00', '2025-03-14 11:15:00', '2024-2025', 5, 3, 4, 0),
(42, 'aaa1', '2025-03-14 11:30:00', '2025-03-14 13:00:00', '2024-2025', 5, 3, 4, 0),
(43, 'aaa1', '2025-03-14 15:10:00', '2025-03-14 16:40:00', '2024-2025', 5, 3, 4, 0),
(44, 'aaa1', '2025-03-14 17:00:00', '2025-03-14 18:30:00', '2024-2025', 5, 3, 4, 0),
(45, 'GCGP 34', '2025-03-11 08:00:00', '2025-03-11 09:30:00', '2024-2025', 5, 2, 3, 0),
(46, 'GCGP 34', '2025-03-11 09:45:00', '2025-03-11 11:15:00', '2024-2025', 2, 2, 3, 0),
(47, 'siiii', '2025-03-11 17:00:00', '2025-03-11 18:30:00', '2024-2025', 1, 2, 3, 0),
(54, 'sii', '2025-03-12 15:10:00', '2025-03-12 16:40:00', '2024-2025', 1, 2, 3, 0),
(55, 'test', '2025-03-12 08:00:00', '2025-03-12 09:30:00', '2024-2025', 5, 4, 6, 0),
(57, 'test', '2025-03-12 11:30:00', '2025-03-12 13:00:00', '2024-2025', 5, 4, 6, 0),
(58, 'test', '2025-03-12 15:10:00', '2025-03-12 16:40:00', '2024-2025', 5, 4, 6, 0),
(59, 'test', '2025-03-12 17:00:00', '2025-03-12 18:30:00', '2024-2025', 5, 4, 6, 0),
(60, 'corosion', '2025-03-12 08:00:00', '2025-03-12 09:30:00', '2024-2025', 2, 1, 7, 0),
(61, 'corosion', '2025-03-12 09:45:00', '2025-03-12 11:15:00', '2024-2025', 2, 1, 7, 0),
(62, 'corosion', '2025-03-12 11:30:00', '2025-03-12 13:00:00', '2024-2025', 2, 1, 7, 0),
(63, 'corosion', '2025-03-12 15:10:00', '2025-03-12 16:40:00', '2024-2025', 2, 1, 7, 0),
(64, 'corosion', '2025-03-12 17:00:00', '2025-03-12 18:30:00', '2024-2025', 2, 1, 7, 0),
(65, 'GCGP 34', '2025-03-12 08:00:00', '2025-03-12 09:30:00', '2024-2025', 1, 1, 3, 0),
(66, 'tpppp', '2025-03-14 08:00:00', '2025-03-14 09:30:00', '2024-2025', 1, 1, 3, 0),
(68, 'ss', '2025-03-15 08:00:00', '2025-03-15 09:30:00', '2024-2025', 1, 1, 3, 0),
(70, 'aaa', '2025-03-12 08:00:00', '2025-03-12 09:30:00', '2024-2025', 5, 2, 4, 0),
(112, 'cinetique', '2025-03-30 11:30:00', '2025-03-30 13:00:00', '2024-2025', 2, 3, 7, 0),
(114, 'cinetique', '2025-03-30 17:00:00', '2025-03-30 18:30:00', '2024-2025', 2, 3, 7, 1),
(115, 'chimi organic', '2025-03-30 08:00:00', '2025-03-30 09:30:00', '2024-2025', 1, 4, 3, 1),
(116, 'chimi organic', '2025-03-30 09:45:00', '2025-03-30 11:15:00', '2024-2025', 1, 4, 3, 1),
(117, 'chimi organic', '2025-03-30 11:30:00', '2025-03-30 13:00:00', '2024-2025', 1, 4, 3, 0),
(118, 'chimi organic', '2025-03-30 15:10:00', '2025-03-30 16:40:00', '2024-2025', 1, 4, 3, 0),
(119, 'chimi organic', '2025-03-30 17:00:00', '2025-03-30 18:30:00', '2024-2025', 1, 4, 3, 0),
(120, 'gaz natural', '2025-03-30 08:00:00', '2025-03-30 09:30:00', '2024-2025', 6, 1, 6, 0),
(121, 'gaz natural', '2025-03-30 09:45:00', '2025-03-30 11:15:00', '2024-2025', 6, 1, 6, 0),
(123, 'gaz natural', '2025-03-30 15:10:00', '2025-03-30 16:40:00', '2024-2025', 6, 1, 6, 0),
(124, 'gaz natural', '2025-03-30 17:00:00', '2025-03-30 18:30:00', '2024-2025', 6, 1, 6, 0),
(125, 'cinetique', '2025-03-30 09:45:00', '2025-03-30 11:15:00', '2024-2025', 2, 3, 7, 0),
(126, 'gaz natural', '2025-03-30 11:30:00', '2025-03-30 13:00:00', '2024-2025', 6, 1, 6, 0),
(127, 'cinetique', '2025-03-30 15:10:00', '2025-03-30 16:40:00', '2024-2025', 2, 6, 4, 0),
(128, 'cinetique', '2025-04-02 08:00:00', '2025-04-02 09:30:00', '2024-2025', 1, 2, 3, 1),
(129, 'cinetique', '2025-04-02 09:45:00', '2025-04-02 11:15:00', '2024-2025', 1, 2, 3, 1),
(130, 'cinetique', '2025-04-02 11:30:00', '2025-04-02 13:00:00', '2024-2025', 1, 2, 3, 1),
(131, 'cinetique', '2025-04-02 15:10:00', '2025-04-02 16:40:00', '2024-2025', 1, 2, 3, 0),
(132, 'cinetique', '2025-04-02 17:00:00', '2025-04-02 18:30:00', '2024-2025', 1, 2, 3, 1),
(133, 'chimi', '2025-04-02 08:00:00', '2025-04-02 09:30:00', '2024-2025', 5, 1, 7, 1),
(134, 'chimi', '2025-04-02 09:45:00', '2025-04-02 11:15:00', '2024-2025', 5, 1, 7, 1),
(135, 'chimi', '2025-04-02 11:30:00', '2025-04-02 13:00:00', '2024-2025', 5, 1, 7, 1),
(136, 'chimi', '2025-04-02 15:10:00', '2025-04-02 16:40:00', '2024-2025', 5, 1, 7, 1),
(137, 'chimi', '2025-04-02 17:00:00', '2025-04-02 18:30:00', '2024-2025', 5, 1, 7, 1),
(138, 'test', '2025-04-02 08:00:00', '2025-04-02 09:30:00', '2024-2025', 6, 5, 8, 0),
(139, 'test', '2025-04-02 09:45:00', '2025-04-02 11:15:00', '2024-2025', 6, 5, 8, 0),
(140, 'test', '2025-04-02 11:30:00', '2025-04-02 13:00:00', '2024-2025', 6, 5, 8, 0),
(141, 'test', '2025-04-02 15:10:00', '2025-04-02 16:40:00', '2024-2025', 6, 5, 8, 0),
(142, 'test', '2025-04-02 17:00:00', '2025-04-02 18:30:00', '2024-2025', 6, 5, 8, 0),
(143, 'test', '2025-04-02 08:00:00', '2025-04-02 09:30:00', '2024-2025', 2, 5, 6, 0),
(144, 'test', '2025-04-02 09:45:00', '2025-04-02 11:15:00', '2024-2025', 2, 5, 6, 0),
(145, 'test', '2025-04-02 11:30:00', '2025-04-02 13:00:00', '2024-2025', 2, 5, 6, 0),
(146, 'test', '2025-04-02 15:10:00', '2025-04-02 16:40:00', '2024-2025', 2, 5, 6, 0),
(147, 'test', '2025-04-02 17:00:00', '2025-04-02 18:30:00', '2024-2025', 2, 5, 6, 0),
(148, 'aaa', '2025-04-02 08:00:00', '2025-04-02 09:30:00', '2024-2025', 7, 6, 4, 1),
(149, 'aaa', '2025-04-02 09:45:00', '2025-04-02 11:15:00', '2024-2025', 7, 6, 4, 0),
(150, 'aaa', '2025-04-02 11:30:00', '2025-04-02 13:00:00', '2024-2025', 7, 6, 4, 1),
(151, 'aaa', '2025-04-02 15:10:00', '2025-04-02 16:40:00', '2024-2025', 7, 6, 4, 0),
(153, 'acier', '2025-04-02 08:00:00', '2025-04-02 09:30:00', '2024-2025', 8, 4, 9, 0),
(154, 'acier', '2025-04-02 09:45:00', '2025-04-02 11:15:00', '2024-2025', 8, 4, 9, 0),
(155, 'acier', '2025-04-02 11:30:00', '2025-04-02 13:00:00', '2024-2025', 8, 4, 9, 0),
(156, 'acier', '2025-04-02 15:10:00', '2025-04-02 16:40:00', '2024-2025', 8, 4, 9, 0),
(157, 'acier', '2025-04-02 17:00:00', '2025-04-02 18:30:00', '2024-2025', 8, 4, 9, 0),
(159, 'dm`1', '2025-04-03 09:45:00', '2025-04-03 11:15:00', '2024-2025', 6, 6, 8, 0),
(160, 'dm`1', '2025-04-03 11:30:00', '2025-04-03 13:00:00', '2024-2025', 6, 6, 8, 1),
(161, 'dm`1', '2025-04-03 15:10:00', '2025-04-03 16:40:00', '2024-2025', 6, 6, 8, 1),
(162, 'dm`1', '2025-04-03 17:00:00', '2025-04-03 18:30:00', '2024-2025', 6, 6, 8, 1),
(163, 'chimi', '2025-04-02 17:00:00', '2025-04-02 18:30:00', '2024-2025', 7, 4, 4, 0),
(164, 'cinetique1', '2025-04-03 08:00:00', '2025-04-03 09:30:00', '2024-2025', 6, 6, 8, 1),
(165, 'ss', '2025-04-04 08:00:00', '2025-04-04 09:30:00', '2024-2025', 2, 1, 3, 0),
(166, 'ss', '2025-04-04 09:45:00', '2025-04-04 11:15:00', '2024-2025', 2, 1, 3, 0),
(167, 'ss', '2025-04-04 11:30:00', '2025-04-04 13:00:00', '2024-2025', 2, 1, 3, 0);

-- --------------------------------------------------------

--
-- Table structure for table `type`
--

DROP TABLE IF EXISTS `type`;
CREATE TABLE IF NOT EXISTS `type` (
  `id_type` int NOT NULL AUTO_INCREMENT,
  `nom_type` varchar(50) NOT NULL,
  `id_categorie` int NOT NULL,
  PRIMARY KEY (`id_type`),
  KEY `id_categorie` (`id_categorie`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `type`
--

INSERT INTO `type` (`id_type`, `nom_type`, `id_categorie`) VALUES
(1, 'pippet', 1),
(2, 'acide', 4),
(3, 'base', 4),
(4, 'bêcher', 1),
(5, 'climatuseur', 5);

-- --------------------------------------------------------

--
-- Table structure for table `utilisateur`
--

DROP TABLE IF EXISTS `utilisateur`;
CREATE TABLE IF NOT EXISTS `utilisateur` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','user') NOT NULL DEFAULT 'user',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `utilisateur`
--

INSERT INTO `utilisateur` (`id`, `username`, `password`, `role`) VALUES
(5, 'admin', 'scrypt:32768:8:1$clT7v7hQyqaPkQ83$0743f96b5698e29ffc2676ee08cedbd34c8cc0bf8db7efa837e9b25cf83f6571328253133930b672ab32544846bc62f95ee432a474ac602ee8764f866210d0c3', 'admin'),
(6, 'user', 'scrypt:32768:8:1$8eOYiv0OZoQkVAjs$a162834f8313d9950b5547da4961549423e968a4b03d7b03d9c6fb815fc07efc717c8019b18e6c0a28dda15f865f97219090906d555894b94fe4153b045d3e61', 'user');

--
-- Constraints for dumped tables
--

--
-- Constraints for table `article`
--
ALTER TABLE `article`
  ADD CONSTRAINT `article_ibfk_2` FOREIGN KEY (`id_type`) REFERENCES `type` (`id_type`);

--
-- Constraints for table `ligne_recu`
--
ALTER TABLE `ligne_recu`
  ADD CONSTRAINT `ligne_recu_ibfk_1` FOREIGN KEY (`id_article`) REFERENCES `article` (`id_article`) ON DELETE CASCADE,
  ADD CONSTRAINT `ligne_recu_ibfk_2` FOREIGN KEY (`id_recu`) REFERENCES `recu` (`id_recu`) ON DELETE CASCADE;

--
-- Constraints for table `recu`
--
ALTER TABLE `recu`
  ADD CONSTRAINT `recu_ibfk_1` FOREIGN KEY (`id_tp`) REFERENCES `tp` (`id_tp`),
  ADD CONSTRAINT `recu_ibfk_2` FOREIGN KEY (`id_prof`) REFERENCES `professeur` (`id_prof`);

--
-- Constraints for table `stock_laboratoire`
--
ALTER TABLE `stock_laboratoire`
  ADD CONSTRAINT `stock_laboratoire_ibfk_1` FOREIGN KEY (`id_lot`) REFERENCES `stock_magasin` (`id_lot`),
  ADD CONSTRAINT `stock_laboratoire_ibfk_2` FOREIGN KEY (`id_laboratoire`) REFERENCES `laboratoire` (`id_laboratoire`);

--
-- Constraints for table `stock_magasin`
--
ALTER TABLE `stock_magasin`
  ADD CONSTRAINT `stock_magasin_ibfk_1` FOREIGN KEY (`id_article`) REFERENCES `article` (`id_article`);

--
-- Constraints for table `tp`
--
ALTER TABLE `tp`
  ADD CONSTRAINT `tp_ibfk_1` FOREIGN KEY (`id_laboratoire`) REFERENCES `laboratoire` (`id_laboratoire`),
  ADD CONSTRAINT `tp_ibfk_2` FOREIGN KEY (`id_matiere`) REFERENCES `matiere` (`id_matiere`),
  ADD CONSTRAINT `tp_ibfk_3` FOREIGN KEY (`id_prof`) REFERENCES `professeur` (`id_prof`);

--
-- Constraints for table `type`
--
ALTER TABLE `type`
  ADD CONSTRAINT `type_ibfk_1` FOREIGN KEY (`id_categorie`) REFERENCES `categorie` (`id_categorie`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
