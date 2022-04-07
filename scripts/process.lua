-- Data processing based on openmaptiles.org schema
-- https://openmaptiles.org/schema/
-- Copyright (c) 2016, KlokanTech.com & OpenMapTiles contributors.
-- Used under CC-BY 4.0

--------
-- Alter these lines to control which languages are written for place/streetnames
--
-- Preferred language can be (for example) "en" for English, "de" for German, or nil to use OSM's name tag:
preferred_language = "en"
-- This is written into the following vector tile attribute (usually "name:latin"):
preferred_language_attribute = "name_en"
-- If OSM's name tag differs, then write it into this attribute (usually "name_int"):
default_language_attribute = "name_int"
-- Also write these languages if they differ - for example, { "de", "fr" }
additional_languages = { }
--------

-- Enter/exit Tilemaker
function init_function()
end
function exit_function()
end

-- Implement Sets in tables
function Set(list)
	local set = {}
	for _, l in ipairs(list) do set[l] = true end
	return set
end

-- Meters per pixel if tile is 256x256
ZRES5  = 4891.97
ZRES6  = 2445.98
ZRES7  = 1222.99
ZRES8  = 611.5
ZRES9  = 305.7
ZRES10 = 152.9
ZRES11 = 76.4
ZRES12 = 38.2
ZRES13 = 19.1

-- The height of one floor, in meters
BUILDING_FLOOR_HEIGHT = 3.66

-- Process node/way tags

-- Process node tags

node_keys = { "natural", "place" }
function node_function(node)

	-- Write 'place'
	local place = node:Find("place")
	if place ~= "" then
		local mz = 13
		local pop = tonumber(node:Find("population")) or 0

		if     place == "city"                 then mz=5
		elseif place == "town" and pop>8000    then mz=7
		elseif place == "town"                 then mz=8
		elseif place == "village" and pop>3000 then mz=9
		else                                   return
		end

		node:Layer("place", false)
		node:Attribute("class", place)
		node:MinZoom(mz)
		SetNameAttributes(node)
		return
	end

	-- Write 'mountain_peak'
	local natural = node:Find("natural")
	if natural == "peak" or natural == "volcano" then
		node:Layer("mountain_peak", false)
		SetEleAttributes(node)
		node:AttributeNumeric("rank", 1)
		node:Attribute("class", natural)
		SetNameAttributes(node)
		return
	end

end

-- Process way tags

majorRoadValues = Set { "motorway", "trunk", "primary" }
mainRoadValues  = Set { "secondary", "motorway_link", "trunk_link", "primary_link", "secondary_link" }
midRoadValues   = Set { "tertiary", "tertiary_link" }
minorRoadValues = Set { "unclassified", "residential", "road", "living_street" }
trackValues     = Set { "cycleway", "byway", "bridleway", "track" }
pathValues      = Set { "footway", "path", "steps", "pedestrian" }
linkValues      = Set { "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link" }
constructionValues = Set { "primary", "secondary", "tertiary", "motorway", "service", "trunk", "track" }

aerowayBuildings= Set { "terminal", "gate", "tower" }
landuseKeys     = Set { "school", "university", "kindergarten", "college", "library", "hospital",
                        "railway", "cemetery", "military", "residential", "commercial", "industrial",
                        "retail", "stadium", "pitch", "playground", "theme_park", "bus_station", "zoo" }
landcoverKeys   = { wood="wood", forest="wood", rock="rock", bare_rock="rock",
                    wetland="wetland",
                    beach="sand", sand="sand",
                    farmland="farmland", farm="farmland", orchard="farmland", vineyard="farmland", plant_nursery="farmland",
                    glacier="ice", ice_shelf="ice",
                    grassland="grass", grass="grass", meadow="grass", allotments="grass", park="grass", village_green="grass", recreation_ground="grass", garden="grass", golf_course="grass" }

-- POI "class" values: based on https://github.com/openmaptiles/openmaptiles/blob/master/layers/poi/poi.yaml
waterClasses    = Set { "river", "riverbank", "stream", "canal", "drain", "ditch", "dock" }
waterwayClasses = Set { "stream", "river", "canal", "drain", "ditch" }

-- Scan relations for use in ways

function relation_scan_function(relation)
	if relation:Find("type")=="boundary" and relation:Find("boundary")=="administrative" then
		relation:Accept()
	end
end

-- Process way tags

function way_function(way)
	local aerialway = way:Find("aerialway")
	local route    = way:Find("route")
	local highway  = way:Find("highway")
	local waterway = way:Find("waterway")
	local water    = way:Find("water")
	local building = way:Find("building")
	local natural  = way:Find("natural")
	local historic = way:Find("historic")
	local landuse  = way:Find("landuse")
	local leisure  = way:Find("leisure")
	local amenity  = way:Find("amenity")
	local aeroway  = way:Find("aeroway")
	local railway  = way:Find("railway")
	local service  = way:Find("service")
	local sport    = way:Find("sport")
	local shop     = way:Find("shop")
	local tourism  = way:Find("tourism")
	local man_made = way:Find("man_made")
	local boundary = way:Find("boundary")
	local isClosed = way:IsClosed()
	local housenumber = way:Find("addr:housenumber")
	local write_name = false
	local construction = way:Find("construction")

	-- Miscellaneous preprocessing
	if way:Find("tunnel") == "yes" then return end
	if way:Find("disused") == "yes" then return end
	if boundary~="" and way:Find("protection_title")=="National Forest" and way:Find("operator")=="United States Forest Service" then return end
	if highway == "proposed" then return end
	if aerowayBuildings[aeroway] then building="yes"; aeroway="" end
	if landuse == "field" then return end
	if landuse == "meadow" and way:Find("meadow")=="agricultural" then landuse="farmland" end

	-- Boundaries within relations
	local admin_level = 11
	local isBoundary = false
	while true do
		local rel = way:NextRelation()
		if not rel then break end
		isBoundary = true
		admin_level = math.min(admin_level, tonumber(way:FindInRelation("admin_level")) or 11)
	end

	-- Boundaries in ways
	if boundary=="administrative" then
		admin_level = math.min(admin_level, tonumber(way:Find("admin_level")) or 11)
		isBoundary = true
	end
	
	-- Administrative boundaries
	if isBoundary and not (way:Find("maritime")=="yes") then
		if admin_level~=2 then return end
		way:Layer("boundary",false)
		way:AttributeNumeric("admin_level", admin_level)
		way:MinZoom(0)
	end

	-- Aerialways
	if aerialway~="" then
		way:Layer("transportation", false)
		way:Attribute("class", "aerialway")
		SetZOrder(way)
		way:MinZoom(10)
	end

	-- Water table -----------------------------------------------

	-- Roads ('transportation' and 'transportation_name', plus 'transportation_name_detail')
	if highway~="" then
		local access = way:Find("access")
		if access=="private" or access=="no" then return end

		local h = highway
		local minzoom = 99
		local layer = "transportation"
		if majorRoadValues[highway] then              minzoom = 4 end
		if highway == "trunk"       then              minzoom = 5
		elseif highway == "primary" then              minzoom = 7 end
		if mainRoadValues[highway]  then              minzoom = 9 end
		if midRoadValues[highway]   then              minzoom = 11 end
		if minorRoadValues[highway] then h = "minor"; minzoom = 12 end
		if trackValues[highway]     then h = "track"; minzoom = 14 end
		if pathValues[highway]      then h = "path" ; minzoom = 14 end
		if h=="service"             then              minzoom = 12 end

		-- Links (ramp)
		local ramp=false
		if linkValues[highway] then
			splitHighway = split(highway, "_")
			highway = splitHighway[1]; h = highway
			ramp = true
			minzoom = 11
		end

		-- Construction
		if highway == "construction" then return end

		-- Write to layer
		if minzoom <= 14 then
			way:Layer(layer, false)
			way:MinZoom(minzoom)
			SetZOrder(way)
			way:Attribute("class", h)
			SetBrunnelAttributes(way)
			if ramp then way:AttributeNumeric("ramp",1) end

			-- Service
			if highway == "service" and service ~="" then way:Attribute("service", service) end

			-- Write names
			if minzoom < 8 then
				minzoom = 8
			end
			if highway == "motorway" or highway == "trunk" then
				way:Layer("transportation_name", false)
				way:MinZoom(minzoom)
			elseif h == "minor" or h == "track" or h == "path" or h == "service" then
--				way:Layer("transportation_name_detail", false)
				way:MinZoom(minzoom)
			else
				way:Layer("transportation_name_mid", false)
				way:MinZoom(minzoom)
			end
			SetNameAttributes(way)
			way:Attribute("class",h)
			way:Attribute("network","road") -- **** could also be us-interstate, us-highway, us-state
			if h~=highway then way:Attribute("subclass",highway) end
			local ref = way:Find("ref")
			if ref~="" then
				way:Attribute("ref",ref)
				way:AttributeNumeric("ref_length",ref:len())
			end
		end
	end

	-- Railways ('transportation' and 'transportation_name', plus 'transportation_name_detail')
	if railway~="" then
		way:Layer("transportation", false)
		way:Attribute("class", railway)
		SetZOrder(way)
		SetBrunnelAttributes(way)
		if service~="" then
			way:Attribute("service", service)
			way:MinZoom(12)
		else
			way:MinZoom(9)
		end
	end

	-- 'Aeroway'
	if aeroway~="" then
		way:Layer("aeroway", isClosed)
		way:Attribute("class",aeroway)
		way:Attribute("ref",way:Find("ref"))
		write_name = true
	end

	-- 'aerodrome_label'
	if aeroway=="aerodrome" then return end

	-- Set 'waterway' and associated
	if waterwayClasses[waterway] and not isClosed then
		if waterway == "river" and way:Holds("name") then
			way:Layer("waterway", false)
		else
			way:Layer("waterway_detail", false)
		end
		way:Attribute("class", waterway)
		SetNameAttributes(way)
	end

	-- Set names on rivers
	if waterwayClasses[waterway] and not isClosed then
		if waterway == "river" and way:Holds("name") then
			way:Layer("water_name", false)
		end
		way:Attribute("class", waterway)
		SetNameAttributes(way)
	end

	-- Set 'building' and associated
	if building~="" then return end

	-- Set 'housenumber'
	if housenumber~="" then return end

	-- Set 'water'
	if natural=="water" or natural=="bay" or leisure=="swimming_pool" or landuse=="reservoir" or landuse=="basin" or waterClasses[waterway] then
		if way:Find("covered")=="yes" or not isClosed then return end
		local class="lake"; if natural=="bay" then 
			class="ocean" 
		elseif waterway~="" then 
			class="river" 
		end
		if class=="lake" and way:Find("wikidata")=="Q192770" then return end
		if class=="ocean" and isClosed and (way:AreaIntersecting("ocean")/way:Area() > 0.98) then return end
		way:Layer("water",true)
		SetMinZoomByArea(way)
		way:Attribute("class",class)

		if way:Holds("name") and natural=="water" and water ~= "basin" and water ~= "wastewater" then
			way:LayerAsCentroid("water_name_detail")
			SetNameAttributes(way)
			SetMinZoomByArea(way)
			way:Attribute("class", class)
		end

		return -- in case we get any landuse processing
	end

	-- Set 'landcover' (from landuse, natural, leisure)
	local l = landuse
	if l=="" then l=natural end
	if l=="" then l=leisure end
	if landcoverKeys[l] then
		way:Layer("landcover", true)
		SetMinZoomByArea(way)
		way:Attribute("class", landcoverKeys[l])
		write_name = true
	end

	-- Catch-all
--	if (building~="" or write_name) and way:Holds("name") then
--		way:LayerAsCentroid("poi_detail")
--		SetNameAttributes(way)
--		if write_name then rank=6 else rank=25 end
--		way:AttributeNumeric("rank", rank)
--	end
end

-- Remap coastlines
function attribute_function(attr,layer)
	if attr["featurecla"]=="Glaciated areas" then
		return { subclass="glacier" }
	elseif attr["featurecla"]=="Antarctic Ice Shelf" then
		return { subclass="ice_shelf" }
	elseif attr["featurecla"]=="Urban area" then
		return { class="residential" }
	else
		return { class="ocean" }
	end
end

-- ==========================================================
-- Common functions

-- Write a way centroid to POI layer
function WritePOI(obj,class,subclass,rank)
	local layer = "poi"
	if rank>4 then layer="poi_detail" end
	obj:LayerAsCentroid(layer)
	SetNameAttributes(obj)
	obj:AttributeNumeric("rank", rank)
	obj:Attribute("class", class)
	obj:Attribute("subclass", subclass)
end

-- Set name attributes on any object
function SetNameAttributes(obj)
	local name = obj:Find("name"), iname
	local main_written = name
	-- if we have a preferred language, then write that (if available), and additionally write the base name tag
	if preferred_language and obj:Holds("name:"..preferred_language) then
		iname = obj:Find("name:"..preferred_language)
		obj:Attribute(preferred_language_attribute, iname)
		if iname~=name and default_language_attribute then
			obj:Attribute(default_language_attribute, name)
		else main_written = iname end
	else
		obj:Attribute(preferred_language_attribute, name)
	end
	-- then set any additional languages
	for i,lang in ipairs(additional_languages) do
		iname = obj:Find("name:"..lang)
		if iname=="" then iname=name end
		if iname~=main_written then obj:Attribute("name:"..lang, iname) end
	end
end

-- Set ele and ele_ft on any object
function SetEleAttributes(obj)
    local ele = obj:Find("ele")
	if ele ~= "" then
		local meter = math.floor(tonumber(ele) or 0)
		local feet = math.floor(meter * 3.2808399)
		obj:AttributeNumeric("ele", meter)
		obj:AttributeNumeric("ele_ft", feet)
    end
end

function SetBrunnelAttributes(obj)
	if     obj:Find("bridge") == "yes" then obj:Attribute("brunnel", "bridge")
	elseif obj:Find("tunnel") == "yes" then obj:Attribute("brunnel", "tunnel")
	elseif obj:Find("ford")   == "yes" then obj:Attribute("brunnel", "ford")
	end
end

-- Set minimum zoom level by area
function SetMinZoomByArea(way)
	local area=way:Area()
	if     area>ZRES5^2  then way:MinZoom(6)
	elseif area>ZRES6^2  then way:MinZoom(7)
	elseif area>ZRES7^2  then way:MinZoom(8)
	elseif area>ZRES8^2  then way:MinZoom(9)
	elseif area>ZRES9^2  then way:MinZoom(10)
	elseif area>ZRES10^2 then way:MinZoom(11)
	elseif area>ZRES11^2 then way:MinZoom(12)
	elseif area>ZRES12^2 then way:MinZoom(13)
	else                      way:MinZoom(14) end
end

-- Implement z_order as calculated by Imposm
-- See https://imposm.org/docs/imposm3/latest/mapping.html#wayzorder for details.
function SetZOrder(way)
	local highway = way:Find("highway")
	local layer = tonumber(way:Find("layer"))
	local bridge = way:Find("bridge")
	local tunnel = way:Find("tunnel")
	local zOrder = 0
	if bridge ~= "" and bridge ~= "no" then
		zOrder = zOrder + 10
	elseif tunnel ~= "" and tunnel ~= "no" then
		zOrder = zOrder - 10
	end
	if not (layer == nil) then
		if layer > 7 then
			layer = 7
		elseif layer < -7 then
			layer = -7
		end
		zOrder = zOrder + layer * 10
	end
	local hwClass = 0
	-- See https://github.com/omniscale/imposm3/blob/53bb80726ca9456e4a0857b38803f9ccfe8e33fd/mapping/columns.go#L251
	if highway == "motorway" then
		hwClass = 9
	elseif highway == "trunk" then
		hwClass = 8
	elseif highway == "primary" then
		hwClass = 6
	elseif highway == "secondary" then
		hwClass = 5
	elseif highway == "tertiary" then
		hwClass = 4
	else
		hwClass = 3
	end
	zOrder = zOrder + hwClass
	way:ZOrder(zOrder)
end

-- ==========================================================
-- Lua utility functions

function split(inputstr, sep) -- https://stackoverflow.com/a/7615129/4288232
	if sep == nil then
		sep = "%s"
	end
	local t={} ; i=1
	for str in string.gmatch(inputstr, "([^"..sep.."]+)") do
		t[i] = str
		i = i + 1
	end
	return t
end

-- vim: tabstop=2 shiftwidth=2 noexpandtab
