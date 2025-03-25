-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1:3306
-- Généré le : mar. 25 mars 2025 à 00:49
-- Version du serveur : 5.6.17
-- Version de PHP : 8.3.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `gestion_lab`
--

-- --------------------------------------------------------

--
-- Structure de la table `article`
--

DROP TABLE IF EXISTS `article`;
CREATE TABLE IF NOT EXISTS `article` (
  `id_article` int(11) NOT NULL AUTO_INCREMENT,
  `nom_article` varchar(150) NOT NULL,
  `unite_mesure` varchar(50) NOT NULL,
  `date_expiration` datetime DEFAULT NULL,
  `id_type` int(11) NOT NULL,
  PRIMARY KEY (`id_article`),
  KEY `id_type` (`id_type`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `article`
--

INSERT INTO `article` (`id_article`, `nom_article`, `unite_mesure`, `date_expiration`, `id_type`) VALUES
(1, 'becher', 'litre', NULL, 1),
(2, 'meden', 'litre', NULL, 1),
(7, 'Diagana', 'litre', '2025-03-23 00:00:00', 1),
(8, 'Diagana', 'kg', '2025-03-25 00:00:00', 1);

-- --------------------------------------------------------

--
-- Structure de la table `categorie`
--

DROP TABLE IF EXISTS `categorie`;
CREATE TABLE IF NOT EXISTS `categorie` (
  `id_categorie` int(11) NOT NULL AUTO_INCREMENT,
  `nom_categorie` varchar(100) NOT NULL,
  PRIMARY KEY (`id_categorie`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `categorie`
--

INSERT INTO `categorie` (`id_categorie`, `nom_categorie`) VALUES
(1, 'materiel'),
(4, 'produit');

-- --------------------------------------------------------

--
-- Structure de la table `historique_`
--

DROP TABLE IF EXISTS `historique_`;
CREATE TABLE IF NOT EXISTS `historique_` (
  `id_historique` int(11) NOT NULL AUTO_INCREMENT,
  `id_tp` int(11) NOT NULL,
  `id_prof` int(11) NOT NULL,
  `degradation` tinyint(1) NOT NULL DEFAULT '0',
  `id_article` int(11) NOT NULL,
  `quantite` int(11) NOT NULL DEFAULT '0',
  `date_utilisation` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `commentaire` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_historique`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure de la table `laboratoire`
--

DROP TABLE IF EXISTS `laboratoire`;
CREATE TABLE IF NOT EXISTS `laboratoire` (
  `id_laboratoire` int(11) NOT NULL AUTO_INCREMENT,
  `nom_laboratoire` varchar(50) NOT NULL,
  `capacite` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_laboratoire`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `laboratoire`
--

INSERT INTO `laboratoire` (`id_laboratoire`, `nom_laboratoire`, `capacite`) VALUES
(1, 'Laboratoire de Chimie', 5),
(2, 'labo cinetique', 8),
(5, 'Petrochimi', 10);

-- --------------------------------------------------------

--
-- Structure de la table `ligne_recu`
--

DROP TABLE IF EXISTS `ligne_recu`;
CREATE TABLE IF NOT EXISTS `ligne_recu` (
  `id_article` int(11) NOT NULL DEFAULT '0',
  `id_recu` int(11) NOT NULL DEFAULT '0',
  `quantite` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_article`,`id_recu`),
  KEY `id_recu` (`id_recu`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure de la table `matiere`
--

DROP TABLE IF EXISTS `matiere`;
CREATE TABLE IF NOT EXISTS `matiere` (
  `id_matiere` int(11) NOT NULL AUTO_INCREMENT,
  `nom_matiere` varchar(100) NOT NULL,
  `niveau` enum('L1','L2','L3') NOT NULL,
  PRIMARY KEY (`id_matiere`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `matiere`
--

INSERT INTO `matiere` (`id_matiere`, `nom_matiere`, `niveau`) VALUES
(1, 'GCGP_41', 'L1'),
(2, 'GCGP_42', 'L3'),
(3, 'chimi cinetique', 'L1'),
(4, 'chimi', 'L3');

-- --------------------------------------------------------

--
-- Structure de la table `professeur`
--

DROP TABLE IF EXISTS `professeur`;
CREATE TABLE IF NOT EXISTS `professeur` (
  `id_prof` int(11) NOT NULL AUTO_INCREMENT,
  `prenom` varchar(50) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `email` varchar(50) NOT NULL,
  `telephone` varchar(15) NOT NULL,
  PRIMARY KEY (`id_prof`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `telephone` (`telephone`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `professeur`
--

INSERT INTO `professeur` (`id_prof`, `prenom`, `nom`, `email`, `telephone`) VALUES
(3, 'yeslem', 'teghra', 'sidahmedmeden07@gmail.com', '34303065'),
(4, 'a', 'a', '07@gmail.com', '00000000'),
(6, 'med', '23', '23543@isme.esp.mre', '34303464'),
(7, 'Dr.ahmed', 'ahmed', 'sidahmedmeden7@gmail.com', '34303445');

-- --------------------------------------------------------

--
-- Structure de la table `recu`
--

DROP TABLE IF EXISTS `recu`;
CREATE TABLE IF NOT EXISTS `recu` (
  `id_recu` int(11) NOT NULL AUTO_INCREMENT,
  `date_emission` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `degradation` tinyint(1) NOT NULL DEFAULT '0',
  `observations` varchar(255) DEFAULT NULL,
  `id_tp` int(11) NOT NULL,
  `id_prof` int(11) NOT NULL,
  PRIMARY KEY (`id_recu`),
  KEY `id_tp` (`id_tp`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure de la table `stock_laboratoire`
--

DROP TABLE IF EXISTS `stock_laboratoire`;
CREATE TABLE IF NOT EXISTS `stock_laboratoire` (
  `id_lot` int(11) NOT NULL,
  `id_laboratoire` int(11) NOT NULL,
  `quantite` int(11) NOT NULL,
  PRIMARY KEY (`id_lot`,`id_laboratoire`),
  KEY `id_laboratoire` (`id_laboratoire`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure de la table `stock_magasin`
--

DROP TABLE IF EXISTS `stock_magasin`;
CREATE TABLE IF NOT EXISTS `stock_magasin` (
  `id_lot` int(11) NOT NULL AUTO_INCREMENT,
  `id_article` int(11) NOT NULL,
  `quantite` int(11) NOT NULL,
  `date_expiration` datetime DEFAULT NULL,
  `date_ajout` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_lot`),
  KEY `id_article` (`id_article`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `stock_magasin`
--

INSERT INTO `stock_magasin` (`id_lot`, `id_article`, `quantite`, `date_expiration`, `date_ajout`) VALUES
(5, 7, 10, '2025-03-23 00:00:00', '2025-03-24 22:31:28'),
(6, 8, 7, '2025-03-25 00:00:00', '2025-03-24 22:31:52');

-- --------------------------------------------------------

--
-- Structure de la table `tp`
--

DROP TABLE IF EXISTS `tp`;
CREATE TABLE IF NOT EXISTS `tp` (
  `id_tp` int(11) NOT NULL AUTO_INCREMENT,
  `nom_tp` varchar(100) NOT NULL,
  `heure_debut` datetime NOT NULL,
  `heure_fin` datetime NOT NULL,
  `annee_scolaire` varchar(9) NOT NULL,
  `id_laboratoire` int(11) NOT NULL,
  `id_matiere` int(11) NOT NULL,
  `id_prof` int(11) NOT NULL,
  PRIMARY KEY (`id_tp`),
  KEY `id_laboratoire` (`id_laboratoire`),
  KEY `id_matiere` (`id_matiere`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB AUTO_INCREMENT=77 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `tp`
--

INSERT INTO `tp` (`id_tp`, `nom_tp`, `heure_debut`, `heure_fin`, `annee_scolaire`, `id_laboratoire`, `id_matiere`, `id_prof`) VALUES
(8, 'aaa', '2025-03-08 08:00:00', '2025-03-08 09:30:00', '2024-2025', 1, 1, 3),
(26, 'aaa', '2025-03-11 11:30:00', '2025-03-11 13:00:00', '2024-2025', 1, 3, 3),
(33, 'GCGP 34', '2025-03-10 08:00:00', '2025-03-10 09:30:00', '2024-2025', 1, 1, 3),
(40, 'aaa1', '2025-03-14 08:00:00', '2025-03-14 09:30:00', '2024-2025', 5, 3, 4),
(41, 'aaa1', '2025-03-14 09:45:00', '2025-03-14 11:15:00', '2024-2025', 5, 3, 4),
(42, 'aaa1', '2025-03-14 11:30:00', '2025-03-14 13:00:00', '2024-2025', 5, 3, 4),
(43, 'aaa1', '2025-03-14 15:10:00', '2025-03-14 16:40:00', '2024-2025', 5, 3, 4),
(44, 'aaa1', '2025-03-14 17:00:00', '2025-03-14 18:30:00', '2024-2025', 5, 3, 4),
(45, 'GCGP 34', '2025-03-11 08:00:00', '2025-03-11 09:30:00', '2024-2025', 5, 2, 3),
(46, 'GCGP 34', '2025-03-11 09:45:00', '2025-03-11 11:15:00', '2024-2025', 2, 2, 3),
(47, 'siiii', '2025-03-11 17:00:00', '2025-03-11 18:30:00', '2024-2025', 1, 2, 3),
(54, 'sii', '2025-03-12 15:10:00', '2025-03-12 16:40:00', '2024-2025', 1, 2, 3),
(55, 'test', '2025-03-12 08:00:00', '2025-03-12 09:30:00', '2024-2025', 5, 4, 6),
(57, 'test', '2025-03-12 11:30:00', '2025-03-12 13:00:00', '2024-2025', 5, 4, 6),
(58, 'test', '2025-03-12 15:10:00', '2025-03-12 16:40:00', '2024-2025', 5, 4, 6),
(59, 'test', '2025-03-12 17:00:00', '2025-03-12 18:30:00', '2024-2025', 5, 4, 6),
(60, 'corosion', '2025-03-12 08:00:00', '2025-03-12 09:30:00', '2024-2025', 2, 1, 7),
(61, 'corosion', '2025-03-12 09:45:00', '2025-03-12 11:15:00', '2024-2025', 2, 1, 7),
(62, 'corosion', '2025-03-12 11:30:00', '2025-03-12 13:00:00', '2024-2025', 2, 1, 7),
(63, 'corosion', '2025-03-12 15:10:00', '2025-03-12 16:40:00', '2024-2025', 2, 1, 7),
(64, 'corosion', '2025-03-12 17:00:00', '2025-03-12 18:30:00', '2024-2025', 2, 1, 7),
(65, 'GCGP 34', '2025-03-12 08:00:00', '2025-03-12 09:30:00', '2024-2025', 1, 1, 3),
(66, 'tpppp', '2025-03-14 08:00:00', '2025-03-14 09:30:00', '2024-2025', 1, 1, 3),
(68, 'ss', '2025-03-15 08:00:00', '2025-03-15 09:30:00', '2024-2025', 1, 1, 3),
(70, 'aaa', '2025-03-12 08:00:00', '2025-03-12 09:30:00', '2024-2025', 5, 2, 4),
(71, 'aaa', '2025-03-13 08:00:00', '2025-03-13 09:30:00', '2024-2025', 5, 1, 3),
(72, 'aaa', '2025-03-13 09:45:00', '2025-03-13 11:15:00', '2024-2025', 5, 1, 3),
(73, 'aaa', '2025-03-13 11:30:00', '2025-03-13 13:00:00', '2024-2025', 5, 1, 3),
(74, 'aaa', '2025-03-13 15:10:00', '2025-03-13 16:40:00', '2024-2025', 5, 1, 3),
(75, 'aaa', '2025-03-13 17:00:00', '2025-03-13 18:30:00', '2024-2025', 5, 1, 3),
(76, 'corrosion', '2025-03-18 09:45:00', '2025-03-18 11:15:00', '2024-2025', 1, 2, 3);

-- --------------------------------------------------------

--
-- Structure de la table `type`
--

DROP TABLE IF EXISTS `type`;
CREATE TABLE IF NOT EXISTS `type` (
  `id_type` int(11) NOT NULL AUTO_INCREMENT,
  `nom_type` varchar(50) NOT NULL,
  `id_categorie` int(11) NOT NULL,
  PRIMARY KEY (`id_type`),
  KEY `id_categorie` (`id_categorie`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `type`
--

INSERT INTO `type` (`id_type`, `nom_type`, `id_categorie`) VALUES
(1, 'recipiente', 1);

-- --------------------------------------------------------

--
-- Structure de la table `utilisateur`
--

DROP TABLE IF EXISTS `utilisateur`;
CREATE TABLE IF NOT EXISTS `utilisateur` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','user') NOT NULL DEFAULT 'user',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `utilisateur`
--

INSERT INTO `utilisateur` (`id`, `username`, `password`, `role`) VALUES
(5, 'admin', 'scrypt:32768:8:1$clT7v7hQyqaPkQ83$0743f96b5698e29ffc2676ee08cedbd34c8cc0bf8db7efa837e9b25cf83f6571328253133930b672ab32544846bc62f95ee432a474ac602ee8764f866210d0c3', 'admin'),
(6, 'user', 'scrypt:32768:8:1$8eOYiv0OZoQkVAjs$a162834f8313d9950b5547da4961549423e968a4b03d7b03d9c6fb815fc07efc717c8019b18e6c0a28dda15f865f97219090906d555894b94fe4153b045d3e61', 'user');

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `article`
--
ALTER TABLE `article`
  ADD CONSTRAINT `article_ibfk_2` FOREIGN KEY (`id_type`) REFERENCES `type` (`id_type`);

--
-- Contraintes pour la table `ligne_recu`
--
ALTER TABLE `ligne_recu`
  ADD CONSTRAINT `ligne_recu_ibfk_1` FOREIGN KEY (`id_article`) REFERENCES `article` (`id_article`) ON DELETE CASCADE,
  ADD CONSTRAINT `ligne_recu_ibfk_2` FOREIGN KEY (`id_recu`) REFERENCES `recu` (`id_recu`) ON DELETE CASCADE;

--
-- Contraintes pour la table `recu`
--
ALTER TABLE `recu`
  ADD CONSTRAINT `recu_ibfk_1` FOREIGN KEY (`id_tp`) REFERENCES `tp` (`id_tp`),
  ADD CONSTRAINT `recu_ibfk_2` FOREIGN KEY (`id_prof`) REFERENCES `professeur` (`id_prof`);

--
-- Contraintes pour la table `stock_laboratoire`
--
ALTER TABLE `stock_laboratoire`
  ADD CONSTRAINT `stock_laboratoire_ibfk_1` FOREIGN KEY (`id_lot`) REFERENCES `stock_magasin` (`id_lot`),
  ADD CONSTRAINT `stock_laboratoire_ibfk_2` FOREIGN KEY (`id_laboratoire`) REFERENCES `laboratoire` (`id_laboratoire`);

--
-- Contraintes pour la table `stock_magasin`
--
ALTER TABLE `stock_magasin`
  ADD CONSTRAINT `stock_magasin_ibfk_1` FOREIGN KEY (`id_article`) REFERENCES `article` (`id_article`);

--
-- Contraintes pour la table `tp`
--
ALTER TABLE `tp`
  ADD CONSTRAINT `tp_ibfk_1` FOREIGN KEY (`id_laboratoire`) REFERENCES `laboratoire` (`id_laboratoire`),
  ADD CONSTRAINT `tp_ibfk_2` FOREIGN KEY (`id_matiere`) REFERENCES `matiere` (`id_matiere`),
  ADD CONSTRAINT `tp_ibfk_3` FOREIGN KEY (`id_prof`) REFERENCES `professeur` (`id_prof`);

--
-- Contraintes pour la table `type`
--
ALTER TABLE `type`
  ADD CONSTRAINT `type_ibfk_1` FOREIGN KEY (`id_categorie`) REFERENCES `categorie` (`id_categorie`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
