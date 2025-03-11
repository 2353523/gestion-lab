-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Mar 11, 2025 at 12:59 PM
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
  `id_stock_magasin` int NOT NULL,
  `id_type` int NOT NULL,
  PRIMARY KEY (`id_article`),
  KEY `id_stock_magasin` (`id_stock_magasin`),
  KEY `id_type` (`id_type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `categorie`
--

DROP TABLE IF EXISTS `categorie`;
CREATE TABLE IF NOT EXISTS `categorie` (
  `id_categorie` int NOT NULL AUTO_INCREMENT,
  `nom_categorie` varchar(100) NOT NULL,
  PRIMARY KEY (`id_categorie`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `historique_`
--

DROP TABLE IF EXISTS `historique_`;
CREATE TABLE IF NOT EXISTS `historique_` (
  `id_historique` int NOT NULL AUTO_INCREMENT,
  `id_tp` int NOT NULL,
  `id_prof` int NOT NULL,
  `degradation` tinyint(1) NOT NULL DEFAULT '0',
  `id_article` int NOT NULL,
  `quantite` int NOT NULL DEFAULT '0',
  `date_utilisation` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `commentaire` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_historique`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

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
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `laboratoire`
--

INSERT INTO `laboratoire` (`id_laboratoire`, `nom_laboratoire`, `capacite`) VALUES
(1, 'Laboratoire de Chimie', 5),
(2, 'labo cinetique', 8),
(5, 'Petrochimi', 10);

-- --------------------------------------------------------

--
-- Table structure for table `ligne_recu`
--

DROP TABLE IF EXISTS `ligne_recu`;
CREATE TABLE IF NOT EXISTS `ligne_recu` (
  `id_article` int NOT NULL DEFAULT '0',
  `id_recu` int NOT NULL DEFAULT '0',
  `quantite` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_article`,`id_recu`),
  KEY `id_recu` (`id_recu`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

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
(4, 'chimi', 'L1');

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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `professeur`
--

INSERT INTO `professeur` (`id_prof`, `prenom`, `nom`, `email`, `telephone`) VALUES
(3, 'yeslem', 'teghra', 'sidahmedmeden07@gmail.com', '34303065'),
(4, 'a', 'a', '07@gmail.com', '00000000');

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
  KEY `id_tp` (`id_tp`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `stock_laboratoire`
--

DROP TABLE IF EXISTS `stock_laboratoire`;
CREATE TABLE IF NOT EXISTS `stock_laboratoire` (
  `id_article` int NOT NULL DEFAULT '0',
  `id_laboratoire` int NOT NULL DEFAULT '0',
  `quantite` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_article`,`id_laboratoire`),
  KEY `id_laboratoire` (`id_laboratoire`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `stock_magasin`
--

DROP TABLE IF EXISTS `stock_magasin`;
CREATE TABLE IF NOT EXISTS `stock_magasin` (
  `id_stock_magasin` int NOT NULL AUTO_INCREMENT,
  `quantite` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_stock_magasin`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

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
  PRIMARY KEY (`id_tp`),
  KEY `id_laboratoire` (`id_laboratoire`),
  KEY `id_matiere` (`id_matiere`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `tp`
--

INSERT INTO `tp` (`id_tp`, `nom_tp`, `heure_debut`, `heure_fin`, `annee_scolaire`, `id_laboratoire`, `id_matiere`, `id_prof`) VALUES
(8, 'aaa', '2025-03-08 08:00:00', '2025-03-08 09:30:00', '2024-2025', 1, 1, 3),
(26, 'aaa', '2025-03-11 11:30:00', '2025-03-11 13:00:00', '2024-2025', 1, 3, 3),
(33, 'GCGP 34', '2025-03-10 08:00:00', '2025-03-10 09:30:00', '2024-2025', 1, 1, 3),
(35, 'test2', '2025-03-12 08:00:00', '2025-03-12 09:30:00', '2024-2025', 2, 1, 4),
(36, 'test2', '2025-03-12 09:45:00', '2025-03-12 11:15:00', '2024-2025', 2, 1, 4),
(37, 'test2', '2025-03-12 11:30:00', '2025-03-12 13:00:00', '2024-2025', 2, 1, 4),
(38, 'test2', '2025-03-12 15:10:00', '2025-03-12 16:40:00', '2024-2025', 2, 1, 4),
(39, 'test2', '2025-03-12 17:00:00', '2025-03-12 18:30:00', '2024-2025', 2, 1, 4),
(40, 'aaa1', '2025-03-14 08:00:00', '2025-03-14 09:30:00', '2024-2025', 5, 3, 4),
(41, 'aaa1', '2025-03-14 09:45:00', '2025-03-14 11:15:00', '2024-2025', 5, 3, 4),
(42, 'aaa1', '2025-03-14 11:30:00', '2025-03-14 13:00:00', '2024-2025', 5, 3, 4),
(43, 'aaa1', '2025-03-14 15:10:00', '2025-03-14 16:40:00', '2024-2025', 5, 3, 4),
(44, 'aaa1', '2025-03-14 17:00:00', '2025-03-14 18:30:00', '2024-2025', 5, 3, 4),
(45, 'GCGP 34', '2025-03-11 08:00:00', '2025-03-11 09:30:00', '2024-2025', 5, 2, 3),
(46, 'GCGP 34', '2025-03-11 09:45:00', '2025-03-11 11:15:00', '2024-2025', 2, 2, 3);

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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `utilisateur`
--

INSERT INTO `utilisateur` (`id`, `username`, `password`, `role`) VALUES
(3, 'admin', 'scrypt:32768:8:1$xmmxTqTqqrpQuIy9$a6050327d9d75a52f0c38c73105064bbe9f027455c89ddeb29428cbcd4b635fd19c71b48bdfe93b63cd50f5cc12298f4ab6c9b8a35bcee721ee85f7e2a7b4288', 'admin'),
(4, 'user', 'scrypt:32768:8:1$v8TyVGznbgTZmpfO$5471fb1171e02d10f9e8f88fc6d20f83d6d48ba3ceea9c6028dd7da6502bfcf465e80643bf72c517dbf5c505c4c1677e5290649c5956fe60167e8a1d0e355269', 'user');

--
-- Constraints for dumped tables
--

--
-- Constraints for table `article`
--
ALTER TABLE `article`
  ADD CONSTRAINT `article_ibfk_1` FOREIGN KEY (`id_stock_magasin`) REFERENCES `stock_magasin` (`id_stock_magasin`),
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
  ADD CONSTRAINT `stock_laboratoire_ibfk_1` FOREIGN KEY (`id_article`) REFERENCES `article` (`id_article`) ON DELETE CASCADE,
  ADD CONSTRAINT `stock_laboratoire_ibfk_2` FOREIGN KEY (`id_laboratoire`) REFERENCES `laboratoire` (`id_laboratoire`) ON DELETE CASCADE;

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
