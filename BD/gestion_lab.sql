-- phpMyAdmin SQL Dump
-- version 4.1.14
-- http://www.phpmyadmin.net
--
-- Host: 127.0.0.1
-- Generation Time: Feb 28, 2025 at 01:12 PM
-- Server version: 5.6.17
-- PHP Version: 5.5.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `gestion_lab`
--

-- --------------------------------------------------------

--
-- Table structure for table `article`
--

CREATE TABLE IF NOT EXISTS `article` (
  `id_article` int(11) NOT NULL AUTO_INCREMENT,
  `nom_article` varchar(150) NOT NULL,
  `id_type` int(11) NOT NULL,
  `unite_mesure` varchar(50) NOT NULL,
  `id_recu` int(11) NOT NULL,
  `id_stock_magasin` int(11) NOT NULL,
  `id_type_1` int(11) NOT NULL,
  PRIMARY KEY (`id_article`),
  KEY `id_recu` (`id_recu`),
  KEY `id_stock_magasin` (`id_stock_magasin`),
  KEY `id_type_1` (`id_type_1`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `categorie`
--

CREATE TABLE IF NOT EXISTS `categorie` (
  `id_categorie` int(11) NOT NULL AUTO_INCREMENT,
  `nom_categorie` varchar(100) NOT NULL,
  PRIMARY KEY (`id_categorie`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `historique_`
--

CREATE TABLE IF NOT EXISTS `historique_` (
  `id_historique` int(11) NOT NULL AUTO_INCREMENT,
  `id_tp` int(11) NOT NULL,
  `id_prof` int(11) NOT NULL,
  `degradation` varchar(50) NOT NULL,
  `id_article` int(11) NOT NULL,
  `quantite` int(11) NOT NULL,
  `date_utilisation` datetime NOT NULL,
  `commentaire` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_historique`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `laboratoire`
--

CREATE TABLE IF NOT EXISTS `laboratoire` (
  `id_laboratoire` int(11) NOT NULL AUTO_INCREMENT,
  `nom_laboratoire` varchar(50) NOT NULL,
  PRIMARY KEY (`id_laboratoire`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `matiere`
--

CREATE TABLE IF NOT EXISTS `matiere` (
  `id_matiere` int(11) NOT NULL AUTO_INCREMENT,
  `nom_matiere` varchar(100) NOT NULL,
  PRIMARY KEY (`id_matiere`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `professeur`
--

CREATE TABLE IF NOT EXISTS `professeur` (
  `id_prof` int(11) NOT NULL AUTO_INCREMENT,
  `prenom` varchar(50) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `email` varchar(50) NOT NULL,
  `telephone` varchar(8) NOT NULL,
  PRIMARY KEY (`id_prof`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `telephone` (`telephone`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `recu`
--

CREATE TABLE IF NOT EXISTS `recu` (
  `id_recu` int(11) NOT NULL AUTO_INCREMENT,
  `id_tp` int(11) NOT NULL,
  `id_article_1` int(11) NOT NULL,
  `id_prof` int(11) NOT NULL,
  `date_emission` datetime NOT NULL,
  `degradation` varchar(50) NOT NULL DEFAULT '0',
  `observations` varchar(255) DEFAULT NULL,
  `quantite` int(11) NOT NULL,
  `id_historique` int(11) NOT NULL,
  `id_prof_1` int(11) NOT NULL,
  PRIMARY KEY (`id_recu`),
  KEY `id_historique` (`id_historique`),
  KEY `id_prof_1` (`id_prof_1`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `stock_laboratoire`
--

CREATE TABLE IF NOT EXISTS `stock_laboratoire` (
  `id_article_1` int(11) NOT NULL DEFAULT '0',
  `id_laboratoire_1` int(11) NOT NULL DEFAULT '0',
  `id_stock_labo` int(11) NOT NULL,
  `id_article` int(11) NOT NULL,
  `quantite` int(11) NOT NULL DEFAULT '0',
  `id_laboratoire` int(11) NOT NULL,
  PRIMARY KEY (`id_article_1`,`id_laboratoire_1`),
  KEY `id_laboratoire_1` (`id_laboratoire_1`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `stock_magasin`
--

CREATE TABLE IF NOT EXISTS `stock_magasin` (
  `id_stock_magasin` int(11) NOT NULL AUTO_INCREMENT,
  `id_article` int(11) NOT NULL,
  `quantite` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_stock_magasin`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `tp`
--

CREATE TABLE IF NOT EXISTS `tp` (
  `id_tp` int(11) NOT NULL AUTO_INCREMENT,
  `nom_tp` varchar(100) NOT NULL,
  `heure_debut` datetime NOT NULL,
  `heure_fin` datetime NOT NULL,
  `id_prof` int(11) NOT NULL,
  `id_matiere` int(11) NOT NULL,
  `anne_scolaire` varchar(9) NOT NULL,
  `id_laboratoire` int(11) NOT NULL,
  `id_laboratoire_1` int(11) NOT NULL,
  `id_matiere_1` int(11) NOT NULL,
  `id_prof_1` int(11) NOT NULL,
  PRIMARY KEY (`id_tp`),
  KEY `id_laboratoire_1` (`id_laboratoire_1`),
  KEY `id_matiere_1` (`id_matiere_1`),
  KEY `id_prof_1` (`id_prof_1`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `type`
--

CREATE TABLE IF NOT EXISTS `type` (
  `id_type` int(11) NOT NULL AUTO_INCREMENT,
  `nom_type` varchar(50) NOT NULL,
  `id_categorie` int(11) NOT NULL,
  `id_categorie_1` int(11) NOT NULL,
  PRIMARY KEY (`id_type`),
  KEY `id_categorie_1` (`id_categorie_1`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `article`
--
ALTER TABLE `article`
  ADD CONSTRAINT `article_ibfk_1` FOREIGN KEY (`id_recu`) REFERENCES `recu` (`id_recu`),
  ADD CONSTRAINT `article_ibfk_2` FOREIGN KEY (`id_stock_magasin`) REFERENCES `stock_magasin` (`id_stock_magasin`),
  ADD CONSTRAINT `article_ibfk_3` FOREIGN KEY (`id_type_1`) REFERENCES `type` (`id_type`);

--
-- Constraints for table `recu`
--
ALTER TABLE `recu`
  ADD CONSTRAINT `recu_ibfk_1` FOREIGN KEY (`id_historique`) REFERENCES `historique_` (`id_historique`),
  ADD CONSTRAINT `recu_ibfk_2` FOREIGN KEY (`id_prof_1`) REFERENCES `professeur` (`id_prof`);

--
-- Constraints for table `stock_laboratoire`
--
ALTER TABLE `stock_laboratoire`
  ADD CONSTRAINT `stock_laboratoire_ibfk_1` FOREIGN KEY (`id_article_1`) REFERENCES `article` (`id_article`),
  ADD CONSTRAINT `stock_laboratoire_ibfk_2` FOREIGN KEY (`id_laboratoire_1`) REFERENCES `laboratoire` (`id_laboratoire`);

--
-- Constraints for table `tp`
--
ALTER TABLE `tp`
  ADD CONSTRAINT `tp_ibfk_1` FOREIGN KEY (`id_laboratoire_1`) REFERENCES `laboratoire` (`id_laboratoire`),
  ADD CONSTRAINT `tp_ibfk_2` FOREIGN KEY (`id_matiere_1`) REFERENCES `matiere` (`id_matiere`),
  ADD CONSTRAINT `tp_ibfk_3` FOREIGN KEY (`id_prof_1`) REFERENCES `professeur` (`id_prof`);

--
-- Constraints for table `type`
--
ALTER TABLE `type`
  ADD CONSTRAINT `type_ibfk_1` FOREIGN KEY (`id_categorie_1`) REFERENCES `categorie` (`id_categorie`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
