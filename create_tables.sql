CREATE TABLE `config` (
  `idConfig` int NOT NULL AUTO_INCREMENT,
  `keyword` varchar(180) NOT NULL,
  `maxPages` int NOT NULL,
  `createdAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idConfig`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `domain` (
  `idDomain` int NOT NULL AUTO_INCREMENT,
  `netloc` varchar(100) NOT NULL,
  `blackListed` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`idDomain`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `page` (
  `idPage` int NOT NULL AUTO_INCREMENT,
  `url` varchar(300) NOT NULL,
  `lastAccess` timestamp NULL DEFAULT NULL,
  `hasTitle` tinyint(1) DEFAULT NULL,
  `hasDescription` tinyint(1) DEFAULT NULL,
  `hasKeywords` tinyint(1) DEFAULT NULL,
  `hasAccessibility` tinyint(1) DEFAULT NULL,
  `hasViewport` tinyint(1) DEFAULT NULL,
  `idDomain` int DEFAULT NULL,
  PRIMARY KEY (`idPage`),
  KEY `idDomain_idx` (`idDomain`),
  CONSTRAINT `idDomain` FOREIGN KEY (`idDomain`) REFERENCES `domain` (`idDomain`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `result` (
  `idResult` int NOT NULL AUTO_INCREMENT,
  `idSearch` int DEFAULT NULL,
  `matchesInBody` int DEFAULT NULL,
  `keywordInTitle` smallint DEFAULT '0',
  `keywordInH1` smallint DEFAULT NULL,
  `keywordInDescription` smallint DEFAULT NULL,
  PRIMARY KEY (`idResult`),
  KEY `idSearch_idx` (`idSearch`),
  CONSTRAINT `idSearch` FOREIGN KEY (`idSearch`) REFERENCES `search` (`idSearch`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `search` (
  `idSearch` int NOT NULL AUTO_INCREMENT,
  `idConfig` int NOT NULL,
  `idPage` int NOT NULL,
  `IdMatches` int NOT NULL,
  `score` int DEFAULT NULL,
  PRIMARY KEY (`idSearch`),
  KEY `idConfig_idx` (`idConfig`),
  KEY `idPage_idx` (`idPage`),
  CONSTRAINT `idConfig` FOREIGN KEY (`idConfig`) REFERENCES `config` (`idConfig`),
  CONSTRAINT `idPage` FOREIGN KEY (`idPage`) REFERENCES `page` (`idPage`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
