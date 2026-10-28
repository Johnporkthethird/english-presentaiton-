-- Puts the uploaded showcase skyboxes into levels 1-10. Run once in Roblox Studio's command bar, then save the place.
--
-- 1. Upload the 60 images in skies/upload (Asset Manager > Bulk Import). Each file is named <level>_<face>.png (or .jpg).
-- 2. Either paste each image's asset id below (Asset Manager > right-click the image > Copy Asset ID),
--    or drag the uploaded images into the place as Decals and leave their names as they are: any Decal or Texture
--    named like "L01_sugar_rush_bk" is picked up automatically.
-- 3. Run this script. It prints how many faces it set; a level switches to its sky once all six faces are set.
local IDS = {
	L01_sugar_rush = { bk = 0, dn = 0, ft = 0, lf = 0, rt = 0, up = 0 },
	L02_drive_thru = { bk = 0, dn = 0, ft = 0, lf = 0, rt = 0, up = 0 },
	L03_spore_springs = { bk = 0, dn = 0, ft = 0, lf = 0, rt = 0, up = 0 },
	L04_checkmate = { bk = 0, dn = 0, ft = 0, lf = 0, rt = 0, up = 0 },
	L05_tick_tock = { bk = 0, dn = 0, ft = 0, lf = 0, rt = 0, up = 0 },
	L06_toy_box = { bk = 0, dn = 0, ft = 0, lf = 0, rt = 0, up = 0 },
	L07_orbit = { bk = 0, dn = 0, ft = 0, lf = 0, rt = 0, up = 0 },
	L08_eruption = { bk = 0, dn = 0, ft = 0, lf = 0, rt = 0, up = 0 },
	L09_frostbite = { bk = 0, dn = 0, ft = 0, lf = 0, rt = 0, up = 0 },
	L10_high_score = { bk = 0, dn = 0, ft = 0, lf = 0, rt = 0, up = 0 },
}
local FACE = { bk = "SkyboxBk", dn = "SkyboxDn", ft = "SkyboxFt", lf = "SkyboxLf", rt = "SkyboxRt", up = "SkyboxUp" }

-- ids from Decals / Textures already in the place, by name
for _, d in ipairs(game:GetDescendants()) do
	if d:IsA("Decal") or d:IsA("Texture") then
		local key, face = string.match(d.Name, "^(L%d%d_[%a_]+)_(%a%a)$")
		local id = tonumber(string.match(d.Texture, "(%d+)$") or "")
		if key and IDS[key] and FACE[face] and id and (IDS[key][face] or 0) == 0 then IDS[key][face] = id end
	end
end

local pool = game:GetService("ServerStorage"):FindFirstChild("OBBY_POOL")
local set, levels = 0, 0
for key, faces in pairs(IDS) do
	local n = tonumber(string.sub(key, 2, 3))
	local complete = true
	for f in pairs(FACE) do if (faces[f] or 0) == 0 then complete = false end end
	if complete then
		local targets = {}
		local unit = pool and pool:FindFirstChild(string.format("L%03d", n))
		if unit and unit:FindFirstChild("Level") then table.insert(targets, unit.Level) end
		for _, c in ipairs(workspace:GetChildren()) do
			if c:GetAttribute("ObbyLook") == string.format("sc%03d", n) then table.insert(targets, c) end
		end
		for f, prop in pairs(FACE) do
			for _, t in ipairs(targets) do t:SetAttribute("Lt_Sky_" .. prop, "rbxassetid://" .. faces[f]) end
			set += 1
		end
		levels += 1
	end
end
print(string.format("Showcase skies: %d of 10 levels set (%d faces). Save the place to keep them.", levels, set))
