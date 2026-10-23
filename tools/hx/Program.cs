using LibHac; using LibHac.Common; using LibHac.Common.Keys; using LibHac.Fs; using LibHac.Fs.Fsa; using LibHac.FsSystem; using LibHac.Tools.FsSystem; using LibHac.Tools.FsSystem.NcaUtils; using LibHac.Spl;
// usage: hx <prod.keys> <title.keys> <nca> <section> <outdir>
var ks = ExternalKeyReader.ReadKeyFile(args[0], args[1]);
using var f = new LocalStorage(args[2], FileAccess.Read);
var nca = new Nca(ks, f);
Console.WriteLine($"type {nca.Header.ContentType} keygen {nca.Header.KeyGeneration}");
int sec = int.Parse(args[3]);
var fs = nca.OpenFileSystem(sec, IntegrityCheckLevel.None);
fs.CopyDirectory(new LocalFileSystem(Directory.CreateDirectory(args[4]).FullName), "/", "/");
Console.WriteLine("done");
